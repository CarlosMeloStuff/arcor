#!/usr/bin/env python

from tf import TransformBroadcaster, transformations
import rospy
from art_calibration import ArtRobotCalibration, ArtCellCalibration
from std_msgs.msg import Bool
from art_msgs.srv import RecalibrateCell, RecalibrateCellResponse
import tf
from std_msgs.msg import Header

from dynamic_reconfigure.server import Server
from art_calibration.cfg import CalibrationConfig
import sensor_msgs.point_cloud2 as pc2


class ArtCalibration(object):

    def __init__(self):
        self.listener = tf.TransformListener()

        self.cells = []
        cell_names = rospy.get_param("~cells").split(",")
        print (cell_names)
        for cell in cell_names:
            cell = cell.strip()

        for cell in cell_names:

            if cell == 'pr2':
                self.cells.append(ArtRobotCalibration('pr2', '/pr2/ar_pose_marker',
                                                      'marker_detected', 'odom_combined',
                                                      cell_names[0] + '_kinect2_link',
                                                      self.listener))
            else:

                self.cells.append(ArtCellCalibration(cell, '/art/' + cell + '/ar_pose_marker',
                                                     'marker_detected', cell + '_kinect2_link',
                                                     cell_names[0] + '_kinect2_link',
                                                     self.listener))  # TODO: kapi hack

        self.calibrated_pub = rospy.Publisher('/art/system/calibrated', Bool,
                                              queue_size=10, latch=True)
        self.calibrated = Bool()
        self.calibrated.data = False
        self.calibrated_sended = False
        self.calibrated_pub.publish(self.calibrated)
        self.recalibrate_cell_service = rospy.Service("/art/system/calibrate_cell", RecalibrateCell,
                                                      self.recalibrate_cell_cb)

        self.broadcaster = TransformBroadcaster()

        self.dynamic_reconfigure_srv = Server(CalibrationConfig, self.dynamic_reconfigure_cb)

    def recalibrate_cell_cb(self, req):
        resp = RecalibrateCellResponse()
        resp.success = False
        cell_name = req.cell_name
        for cell in self.cells:
            if cell.cell_id == cell_name:
                rospy.loginfo('Recalibrating cell: ' + req.cell_name)
                cell.reset_markers_searching()
                resp.success = True
                break
        else:
            resp.error = "Unknown cell"
        return resp

    def publish_calibration(self, rate):
        calibrated = True

        time = rospy.Time.now() + rate.sleep_dur

        for cell in self.cells:
            if cell.calibrated:
                tr = cell.get_transform(cell_id=cell.cell_id)
                if cell.cell_id == "n1":
                    self.broadcaster.sendTransform(tr.translation, tr.rotation,
                                                   time, cell.cell_frame,
                                                   "marker_n1")
                else:
                    self.broadcaster.sendTransform(tr.translation, tr.rotation,
                                                   time, cell.cell_frame,
                                                   cell.world_frame)

            else:
                calibrated = False

        if calibrated and not self.calibrated_sended:
            self.calibrated_sended = True
            self.calibrated.data = True
            self.calibrated_pub.publish(self.calibrated)

    def dynamic_reconfigure_cb(self, config, level):

        for cell in self.cells:  # type: ArtCellCalibration
            cell.x_offset = config.get(cell.cell_id + "_x_offset", 0)
            cell.y_offset = config.get(cell.cell_id + "_y_offset", 0)
            cell.z_offset = config.get(cell.cell_id + "_z_offset", 0)
            cell.x_rotate_offset = config.get(cell.cell_id + "_x_rotate_offset", 0)
            cell.y_rotate_offset = config.get(cell.cell_id + "_y_rotate_offset", 0)
            cell.z_rotate_offset = config.get(cell.cell_id + "_z_rotate_offset", 0)
        return config
