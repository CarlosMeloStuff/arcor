cmake_minimum_required(VERSION 2.8.3)
project(art_bringup)

find_package(catkin REQUIRED COMPONENTS
    roslaunch
    art_db
    art_simple_tracker
    )

catkin_package()

# if (CATKIN_ENABLE_TESTING)
#    roslaunch_add_file_check(launch)
# endif()
