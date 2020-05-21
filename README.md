# GDAL osgeo

	https://gdal.org/python/osgeo.ogr.Geometry-class.html

	https://gdal.org/python/osgeo.ogr-module.html

	https://pcjericks.github.io/py-gdalogr-cookbook/geometry.html

# Change projection

	ogr2ogr Portland.shp -s_srs EPSG:3857 -t_srs EPSG:4326 portland/outfile.shp

# GeoJSON to Shapefile

https://gis.stackexchange.com/questions/68175/converting-geojson-to-shapefile-using-ogr2ogr

	ogr2ogr -nlt POLYGON -skipfailures polygons.shp geojsonfile.json OGRGeoJSON

# Select Features by Attributes

	ogr2ogr -where "ID='1'" outfile.shp infile.shp

or if you have to do more complex query on your input data:

	ogr2ogr -sql "SELECT * FROM infile WHERE ID='1'" outfile.shp infile.shp
	
If ID is a field of Integer type, substitute ID='1' with ID=1.

## Change CRS

	ogr2ogr output.geojson -t_srs "EPSG:4326" CNTR_LB_2016_3857.geojson

## Merge Features

https://gis-pdx.opendata.arcgis.com/datasets/65432a0067f949dd99f3ad0f51f11667_9?geometry=-132.864%2C44.353%2C-113.177%2C47.038

In order to merge all features into one, you should do:

	ogr2ogr output.shp input.shp -dialect sqlite -sql "SELECT ST_Union(geometry) AS geometry FROM input"

where geometry is the special field used in order to represent the geometry of the features in SQLite SQL dialect and input in the SQL statement is the input layer name.

## Notes:

-f "ESRI Shapefile" is not necessary because "ESRI Shapefile" is the ogr2ogr default output format;
it's convenient to skip -select and use directly the -where clause when you want to select all the fields.

### Cities

https://catalog.data.gov/dataset/500-cities-city-boundaries-acd62

