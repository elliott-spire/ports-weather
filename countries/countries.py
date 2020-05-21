#!/usr/bin/env python
# -*- coding: utf-8 -*-

from osgeo import ogr

class Point(object):
    """ Wrapper for ogr point """
    def __init__(self, lat, lng):
        """ Coordinates are in degrees """
        self.point = ogr.Geometry(ogr.wkbPoint)
        self.point.AddPoint(lng, lat)
    
    def getOgr(self):
        return self.point
    ogr = property(getOgr)

class Country(object):
    """ Wrapper for ogr country shape. Not meant to be instantiated directly. """
    def __init__(self, shape):
        self.shape = shape
    
    def getIso(self):
        return self.shape.GetField('ISO2')
    iso = property(getIso)
    
    def __str__(self):
        return self.shape.GetField('NAME')

    def getName(self):
        return self.shape.GetField('NAME')
    NAME = property(getName)

    # Bueller?
    def getCtrNm(self):
        return self.shape.GetField('CNTRY_NAME')
    CNTRY_NAME = property(getCtrNm)
    
    def contains(self, point):
        return self.shape.geometry().Contains(point.ogr)

class CountryChecker(object):
    """ Loads a country shape file, checks coordinates for country location. """
    
    def __init__(self, country_file):
        driver = ogr.GetDriverByName('ESRI Shapefile')
        self.countryFile = driver.Open(country_file)
        self.layer = self.countryFile.GetLayer()
    
    def getCountry(self, point):
        """
        Checks given gps-incoming coordinates for country.
        Output is either country shape index or None
        """
        
        for i in range(self.layer.GetFeatureCount()):
            country = self.layer.GetFeature(i)
            if country.geometry().Contains(point.ogr):
                return Country(country)
        
        # nothing found
        return None

    def getFeature(self, city, state):
        """
        Checks given gps-incoming coordinates for country.
        Output is either country shape index or None
        """
        
        for i in range(self.layer.GetFeatureCount()):
            feature = self.layer.GetFeature(i)
            if city == feature.GetField('NAME') and state == feature.GetField('ST'):
                return feature
        
        # nothing found
        return None

    def getCentroid(self, city, state):
        """
        Returns centroid of given area name
        """
        
        for i in range(self.layer.GetFeatureCount()):
            feature = self.layer.GetFeature(i)
            if city == feature.GetField('NAME') and state == feature.GetField('ST'):
                return feature.geometry().Centroid()

        # nothing found
        return None

    def getPoint(self, lat, lng):
        """
        Returns point geometry from lat/lon
        """
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lng, lat)
        return point
