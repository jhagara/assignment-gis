import psycopg2
from flask import Flask, render_template, g, request, jsonify
app = Flask(__name__)

def connect_db():
    """Connects to the specific database."""
    try:
        conn = psycopg2.connect("dbname='gis' user='postgres' host='localhost' password='postgres'")
    except:
        print("I am unable to connect to the database")
    print("Connencted")
    return conn

def get_db():
    if not hasattr(g, 'posgis'):
        g.postgis = connect_db()
    return g.postgis

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'postgis'):
        g.postgis.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/closest_school')
def closest_school():
    return render_template('closest_school.html')

@app.route('/get_closest_school', methods=['GET'])
def get_closest_school():
    lng = request.args.get("lng")
    lat = request.args.get("lat")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT jsonb_build_object('type','FeatureCollection', 'features', jsonb_agg(feature)) "
                "FROM ( SELECT jsonb_build_object('type', 'Feature', "
                                                 "'id', osm_id, "
                                                 "'geometry', ST_AsGeoJSON(ST_Transform(way, 4326))::jsonb, "
                                                 "'properties', to_jsonb(row) - 'osm_id' - 'way') AS feature "
                        "FROM (select name, way, osm_id, ST_Distance(ST_Transform(ST_GeomFromText('POINT(" + str(lng) + " " + str(lat) + ")',4326),26986), st_transform(way,26986)) "
                        "as dist from planet_osm_polygon where amenity = 'school' ORDER BY dist LIMIT 1) row) features;")

    return jsonify(cur.fetchone())

@app.route('/green_schools')
def green_schools():
    return render_template('green_schools.html')

@app.route('/get_all_green_schools', methods=['GET'])
def get_all_green_schools():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT jsonb_build_object('type',     'FeatureCollection', "
                                          "'features', jsonb_agg(feature) ) "
                    "FROM ( SELECT jsonb_build_object('type',       'Feature', "
                                                     "'id',         osm_id, "
                                                     "'geometry',   ST_AsGeoJSON(ST_Transform(way, 4326))::jsonb, "
                                                     "'properties', to_jsonb(row) - 'osm_id' - 'way' ) AS feature "
                                                    "FROM (select DISTINCT schools.name, schools.osm_id, schools.way "
                                                    "from planet_osm_polygon as schools join planet_osm_polygon as parks on ST_DWithin(st_transform(schools.way,26986), st_transform(parks.way,26986), 100) "
                                                    "where schools.amenity = 'school' and (parks.leisure = 'park' or parks.leisure = 'garden') and st_area(st_transform(parks.way,26986)) > 10) row) features;")

    return jsonify(cur.fetchone())

@app.route('/get_close_stations', methods=['GET'])
def get_close_stations():
    lng = request.args.get("lng")
    lat = request.args.get("lat")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT jsonb_build_object('type',     'FeatureCollection', "
                                          "'features', jsonb_agg(feature) ) "
                                        "FROM ( SELECT jsonb_build_object( 'type',       'Feature', "
                                                                          "'id',         osm_id, "
                                                                          "'geometry',   ST_AsGeoJSON(ST_Transform(way, 4326))::jsonb, "
                                                                          "'properties', to_jsonb(row) - 'osm_id' - 'way') AS feature "
                                                                          "FROM (select name, osm_id, way from planet_osm_point "
                                                                                "where ST_DWithin(ST_Transform(ST_GeomFromText('POINT(" + str(lng) + " " + str(lat) + ")',4326),26986), st_transform(way,26986), 200)  and public_transport='platform') row) features;")

    return jsonify(cur.fetchone())
if __name__ == "__main__":
    app.run()