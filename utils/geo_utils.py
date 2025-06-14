import math


#util for calculating distance between two points
def haversine(lat1, lon1, lat2, lon2):

    R = 6371.0

    #convert decimal degrees to radians
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(math.radians, [lat1, lon1, lat2, lon2])
    
    #calculate the great circle distance in radians
    diff_lat = lat2_rad - lat1_rad
    diff_lon = lon2_rad - lon1_rad


    a = math.sin(diff_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(diff_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    #distance in km
    distance = R * c

    return round(distance, 1)

