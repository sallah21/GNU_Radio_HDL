find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_OOT_HDL gnuradio-OOT_HDL)

FIND_PATH(
    GR_OOT_HDL_INCLUDE_DIRS
    NAMES gnuradio/OOT_HDL/api.h
    HINTS $ENV{OOT_HDL_DIR}/include
        ${PC_OOT_HDL_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_OOT_HDL_LIBRARIES
    NAMES gnuradio-OOT_HDL
    HINTS $ENV{OOT_HDL_DIR}/lib
        ${PC_OOT_HDL_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-OOT_HDLTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_OOT_HDL DEFAULT_MSG GR_OOT_HDL_LIBRARIES GR_OOT_HDL_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_OOT_HDL_LIBRARIES GR_OOT_HDL_INCLUDE_DIRS)
