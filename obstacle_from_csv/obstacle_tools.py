from obstacle_from_csv.aviation_gis_tools.coordinate import *


class Obstacle:

    def __init__(self):
        pass

    @staticmethod
    def parse_obstacle_data(data):
        """ Validate input data.
        Note: Data is valid if:
         - country name is not empty
         - obstacle ident is not empty
         - source longitude can by converted into decimal degrees format - is supported longitude format
         - source latitude can by converted into decimal degrees format - is supported latitude format
         - agl is positive number (integer or float)
         - if amsl is not empty - is a number
         - vert_uom: ft o m
         - obst_type: required
        :param dict: row of CSV data file, from DictReader
        """
        err_msg = ''
        err_msg_list = []
        parsed_data = {}

        ctry_name = data["ctry_name"].strip()
        if ctry_name:
            parsed_data["ctry_name"] = ctry_name
        else:
            err_msg_list.append('Country name is required.')

        obst_ident = data["obst_ident"].strip()
        if obst_ident:
            parsed_data["obst_ident"] = obst_ident
        else:
            err_msg_list.append('Obstacle ident required.')

        parsed_data["obst_name"] = data["obst_name"].strip()

        agl = data["agl"].strip()
        if agl:
            try:
                parsed_data['agl'] = float(agl)
            except ValueError:
                err_msg_list.append('Agl must be a number: {}.'.format(agl))
        else:
            err_msg_list.append('Agl required.')

        amsl = data["amsl"].strip()
        if amsl:
            try:
                parsed_data['amsl'] = float(amsl)
            except ValueError:
                err_msg_list.append('Amsl must be a number: {}.'.format(amsl))

        vert_uom = data["vert_uom"].strip()
        if vert_uom:
            if vert_uom in ['ft', 'm']:
                parsed_data['vert_uom'] = vert_uom
            else:
                err_msg_list.append('Vertical UOM error: {}.'.format(vert_uom))
        else:
            err_msg_list.append('Vertical UOM is required.')

        obst_type = data["obst_type"].strip()
        if obst_type:
            parsed_data["obst_type"] = obst_type
        else:
            err_msg_list.append('Obstacle type is required.')

        lon_src = data["lon_src"].strip()
        if lon_src:
            lon = Coordinate(src_angle=lon_src, angle_type=AT_LONGITUDE)
            lon_dd = lon.convert_to_dd()
            if lon_dd is not None:
                parsed_data["lon_src"] = lon_src
                parsed_data["lon_dd"] = lon_dd
            else:
                err_msg_list.append('Longitude error: {}'.format(lon_src))
        else:
            err_msg_list.append('Longitude is required.')

        lat_src = data["lat_src"].strip()
        if lat_src:
            lat = Coordinate(src_angle=lat_src, angle_type=AT_LATITUDE)
            lat_dd = lat.convert_to_dd()
            if lat_dd is not None:
                parsed_data["lat_src"] = lat_src
                parsed_data["lat_dd"] = lat_dd
            else:
                err_msg_list.append('Latitude error: {}'.format(lat_src))
        else:
            err_msg_list.append('Latitude is required.')

        err_msg = ' '.join(err_msg_list)
        return err_msg, parsed_data
