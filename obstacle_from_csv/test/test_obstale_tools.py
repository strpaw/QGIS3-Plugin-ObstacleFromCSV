import unittest
from obstacle_from_csv.obstacle_tools import *


class ObstacleTests(unittest.TestCase):

    # Test parsing obstacle data - error messages
    def test_ctry_name_required(self):

        data = {
            "ctry_name": "",
            "obst_ident": "1",
            "obst_name": "Test obstacle",
            "lon_src": "1213020.00E",
            "lat_src": "254432.71N",
            "agl": "1",
            "amsl": "3",
            "vert_uom": "ft",
            "obst_type": "Test type"
        }

        msg = Obstacle.parse_obstacle_data(data)[0]
        self.assertEqual('Country name is required.', msg)

    def test_obst_ident_required(self):

        data = {
            "ctry_name": "Test Country",
            "obst_ident": "",
            "obst_name": "Test obstacle",
            "lon_src": "1213020.00E",
            "lat_src": "254432.71N",
            "agl": "1",
            "amsl": "3",
            "vert_uom": "ft",
            "obst_type": "Test type"
        }

        msg = Obstacle.parse_obstacle_data(data)[0]
        self.assertEqual('Obstacle ident required.', msg)

    def test_agl_required(self):

        data = {
            "ctry_name": "Test Country",
            "obst_ident": "Test1",
            "obst_name": "Test obstacle",
            "lon_src": "1213020.00E",
            "lat_src": "254432.71N",
            "agl": "",
            "amsl": "3",
            "vert_uom": "ft",
            "obst_type": "Test type"
        }

        msg = Obstacle.parse_obstacle_data(data)[0]
        self.assertEqual('Agl required.', msg)

    def test_agl_must_be_a_number(self):

        data = {
            "ctry_name": "Test Country",
            "obst_ident": "Test1",
            "obst_name": "Test obstacle",
            "lon_src": "1213020.00E",
            "lat_src": "254432.71N",
            "agl": "1A",
            "amsl": "3",
            "vert_uom": "ft",
            "obst_type": "Test type"
        }

        msg = Obstacle.parse_obstacle_data(data)[0]
        self.assertEqual('Agl must be a number: 1A.', msg)

    def test_amsl_must_be_a_number(self):

        data = {
            "ctry_name": "Test Country",
            "obst_ident": "Test1",
            "obst_name": "Test obstacle",
            "lon_src": "1213020.00E",
            "lat_src": "254432.71N",
            "agl": "1",
            "amsl": "3A",
            "vert_uom": "ft",
            "obst_type": "Test type"
        }

        msg = Obstacle.parse_obstacle_data(data)[0]
        self.assertEqual('Amsl must be a number: 3A.', msg)

    def test_vert_uom_is_required(self):

        data = {
            "ctry_name": "Test Country",
            "obst_ident": "Test1",
            "obst_name": "Test obstacle",
            "lon_src": "1213020.00E",
            "lat_src": "254432.71N",
            "agl": "1",
            "amsl": "3",
            "vert_uom": "  ",
            "obst_type": "Test type"
        }

        msg = Obstacle.parse_obstacle_data(data)[0]
        self.assertEqual('Vertical UOM is required.', msg)

    def test_vert_uom_error(self):

        data = {
            "ctry_name": "Test Country",
            "obst_ident": "Test1",
            "obst_name": "Test obstacle",
            "lon_src": "1213020.00E",
            "lat_src": "254432.71N",
            "agl": "1",
            "amsl": "3",
            "vert_uom": "test",
            "obst_type": "Test type"
        }

        msg = Obstacle.parse_obstacle_data(data)[0]
        self.assertEqual('Vertical UOM error: test.', msg)

    def test_obst_type_is_required(self):

        data = {
            "ctry_name": "Test Country",
            "obst_ident": "Test1",
            "obst_name": "Test obstacle",
            "lon_src": "1213020.00E",
            "lat_src": "254432.71N",
            "agl": "1",
            "amsl": "3",
            "vert_uom": "m",
            "obst_type": " "
        }

        msg = Obstacle.parse_obstacle_data(data)[0]
        self.assertEqual('Obstacle type is required.', msg)

    def test_longitude_required(self):

        data = {
            "ctry_name": "Test Country",
            "obst_ident": "Test1",
            "obst_name": "Test obstacle",
            "lon_src": "",
            "lat_src": "254432.71N",
            "agl": "1",
            "amsl": "3",
            "vert_uom": "m",
            "obst_type": "Test obstacle"
        }

        msg = Obstacle.parse_obstacle_data(data)[0]
        self.assertEqual('Longitude is required.', msg)

    def test_longitude_error(self):

        data = {
            "ctry_name": "Test Country",
            "obst_ident": "Test1",
            "obst_name": "Test obstacle",
            "lon_src": "1213060.00E",
            "lat_src": "254432.71N",
            "agl": "1",
            "amsl": "3",
            "vert_uom": "m",
            "obst_type": "Test obstacle"
        }

        msg = Obstacle.parse_obstacle_data(data)[0]
        self.assertEqual('Longitude error: 1213060.00E', msg)

    def test_latitude_required(self):

        data = {
            "ctry_name": "Test Country",
            "obst_ident": "Test1",
            "obst_name": "Test obstacle",
            "lon_src": "1702034.45E",
            "lat_src": " ",
            "agl": "1",
            "amsl": "3",
            "vert_uom": "m",
            "obst_type": "Test obstacle"
        }

        msg = Obstacle.parse_obstacle_data(data)[0]
        self.assertEqual('Latitude is required.', msg)

    def test_latitude_error(self):

        data = {
            "ctry_name": "Test Country",
            "obst_ident": "Test1",
            "obst_name": "Test obstacle",
            "lon_src": "1213050.00E",
            "lat_src": "254462.71N",
            "agl": "1",
            "amsl": "3",
            "vert_uom": "m",
            "obst_type": "Test obstacle"
        }

        msg = Obstacle.parse_obstacle_data(data)[0]
        self.assertEqual('Latitude error: 254462.71N', msg)

    def test_vert_uom_longitude_error(self):

        data = {
            "ctry_name": "Test Country",
            "obst_ident": "Test1",
            "obst_name": "Test obstacle",
            "lon_src": "1213060.00E",
            "lat_src": "254432.71N",
            "agl": "123",
            "amsl": "355",
            "vert_uom": "test",
            "obst_type": "Test obstacle"
        }

        msg = Obstacle.parse_obstacle_data(data)[0]
        self.assertEqual('Vertical UOM error: test. Longitude error: 1213060.00E', msg)


if __name__ == '__main__':
    unittest.main(verbosity=2)
