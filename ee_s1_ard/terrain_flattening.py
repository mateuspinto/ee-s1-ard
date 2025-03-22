#!/usr/bin/env python3

"""
Version: v1.0
Date: 2021-03-12
Description: This code is adopted from
Vollrath, A., Mullissa, A., & Reiche, J. (2020).
Angular-Based Radiometric Slope Correction for Sentinel-1 on Google Earth Engine.
  Remote Sensing, 12(11), [1867]. https://doi.org/10.3390/rs12111867
"""

import math

import ee

# ---------------------------------------------------------------------------//
# Terrain Flattening
# ---------------------------------------------------------------------------//


def slope_correction(
    collection,
    terrain_flattening_model,
    dem,
    terrain_flattening_additional_layover_shadow_buffer,
):
    """

    Parameters
    ----------
    collection : ee image collection
        DESCRIPTION.
    terrain_flattening_model : string
        The radiometric terrain normalization model, either volume or direct
    DEM : ee asset
        The DEM to be used
    terrain_flattening_additional_layover_shadow_buffer : integer
        The additional buffer to account for the passive layover and shadow

    Returns
    -------
    ee image collection
        An image collection where radiometric terrain normalization is
        implemented on each image

    """

    ninety_rad = ee.Image.constant(90).multiply(math.pi / 180)

    def _volumetric_model_scf(theta_irad, alpha_rrad):
        """

        Parameters
        ----------
        theta_irad : ee.Image
            The scene incidence angle
        alpha_rrad : ee.Image
            Slope steepness in range

        Returns
        -------
        ee.Image
            Applies the volume model in the radiometric terrain normalization

        """

        # Volume model
        nominator = (ninety_rad.subtract(theta_irad).add(alpha_rrad)).tan()
        denominator = (ninety_rad.subtract(theta_irad)).tan()
        return nominator.divide(denominator)

    def _direct_model_scf(theta_irad, alpha_rrad, alpha_azRad):
        """

        Parameters
        ----------
        theta_irad : ee.Image
            The scene incidence angle
        alpha_rrad : ee.Image
            Slope steepness in range

        Returns
        -------
        ee.Image
            Applies the direct model in the radiometric terrain normalization

        """
        # Surface model
        nominator = (ninety_rad.subtract(theta_irad)).cos()
        denominator = alpha_azRad.cos().multiply((ninety_rad.subtract(theta_irad).add(alpha_rrad)).cos())
        return nominator.divide(denominator)

    def _erode(image, distance):
        """


        Parameters
        ----------
        image : ee.Image
            Image to apply the erode function to
        distance : integer
            The distance to apply the buffer

        Returns
        -------
        ee.Image
            An image that is masked to conpensate for passive layover
            and shadow depending on the given distance

        """
        # buffer function (thanks Noel)

        d = image.Not().unmask(1).fastDistanceTransform(30).sqrt().multiply(ee.Image.pixelArea().sqrt())

        return image.updateMask(d.gt(distance))

    def _masking(alpha_rrad, theta_irad, buffer):
        """

        Parameters
        ----------
        alpha_rrad : ee.Image
            Slope steepness in range
        theta_irad : ee.Image
            The scene incidence angle
        buffer : TYPE
            DESCRIPTION.

        Returns
        -------
        ee.Image
            An image that is masked to conpensate for passive layover
            and shadow depending on the given distance

        """
        # calculate masks
        # layover, where slope > radar viewing angle
        layover = alpha_rrad.lt(theta_irad).rename("layover")
        # shadow
        shadow = alpha_rrad.gt(ee.Image.constant(-1).multiply(ninety_rad.subtract(theta_irad))).rename("shadow")
        # combine layover and shadow
        mask = layover.And(shadow)
        # add buffer to final mask
        if buffer > 0:
            mask = _erode(mask, buffer)
        return mask.rename("no_data_mask")

    def _correct(image):
        """


        Parameters
        ----------
        image : ee.Image
            Image to apply the radiometric terrain normalization to

        Returns
        -------
        ee.Image
            Radiometrically terrain corrected image

        """

        band_names = image.bandNames()

        geom = image.geometry()
        proj = image.select(1).projection()

        elevation = dem.resample("bilinear").reproject(proj, None, 10).clip(geom)

        # calculate the look direction
        heading = ee.Terrain.aspect(image.select("angle")).reduceRegion(ee.Reducer.mean(), image.geometry(), 1000)

        # in case of null values for heading replace with 0
        heading = ee.Dictionary(heading).combine({"aspect": 0}, False).get("aspect")

        heading = ee.Algorithms.If(
            ee.Number(heading).gt(180),
            ee.Number(heading).subtract(360),
            ee.Number(heading),
        )

        # the numbering follows the article chapters
        # 2.1.1 Radar geometry
        theta_irad = image.select("angle").multiply(math.pi / 180)
        phi_irad = ee.Image.constant(heading).multiply(math.pi / 180)

        # 2.1.2 Terrain geometry
        alpha_srad = ee.Terrain.slope(elevation).select("slope").multiply(math.pi / 180)

        aspect = ee.Terrain.aspect(elevation).select("aspect").clip(geom)

        aspect_minus = aspect.updateMask(aspect.gt(180)).subtract(360)

        phi_srad = (
            aspect.updateMask(aspect.lte(180)).unmask().add(aspect_minus.unmask()).multiply(-1).multiply(math.pi / 180)
        )

        # elevation = dem.reproject(proj,None, 10).clip(geom)

        # 2.1.3 Model geometry
        # reduce to 3 angle
        phi_rrad = phi_irad.subtract(phi_srad)

        # slope steepness in range (eq. 2)
        alpha_rrad = (alpha_srad.tan().multiply(phi_rrad.cos())).atan()

        # slope steepness in azimuth (eq 3)
        alpha_azRad = (alpha_srad.tan().multiply(phi_rrad.sin())).atan()

        # 2.2
        # Gamma_nought
        gamma0 = image.divide(theta_irad.cos())

        if terrain_flattening_model == "VOLUME":
            # Volumetric Model
            scf = _volumetric_model_scf(theta_irad, alpha_rrad)

        if terrain_flattening_model == "DIRECT":
            scf = _direct_model_scf(theta_irad, alpha_rrad, alpha_azRad)

        # apply model for Gamm0
        gamma0_flat = gamma0.multiply(scf)

        # get Layover/Shadow mask
        mask = _masking(alpha_rrad, theta_irad, terrain_flattening_additional_layover_shadow_buffer)
        output = gamma0_flat.mask(mask).rename(band_names).copyProperties(image)
        output = ee.Image(output).addBands(image.select("angle"), None, True)

        return output.set("system:time_start", image.get("system:time_start"))

    return collection.map(_correct)
