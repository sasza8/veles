PROTOBUF_GENERATE_CPP(PROTO_SRCS PROTO_HDRS network.proto)
if(${CMAKE_VERSION} VERSION_GREATER "3.3.2")
  PROTOBUF_GENERATE_PYTHON(PROTO_PY network.proto)
else(${CMAKE_VERSION} VERSION_GREATER "3.3.2")
  set(PROTO_PY "${CMAKE_CURRENT_BINARY_DIR}/network_pb2.py")
  get_filename_component(ABS_FIL network.proto ABSOLUTE)
  add_custom_command(
    OUTPUT ${PROTO_PY}
    COMMAND  ${PROTOBUF_PROTOC_EXECUTABLE} --python_out ${CMAKE_CURRENT_BINARY_DIR} -I ${CMAKE_CURRENT_SOURCE_DIR} ${ABS_FIL}
    DEPENDS ${ABS_FIL} ${PROTOBUF_PROTOC_EXECUTABLE}
    COMMENT "Running Python protocol buffer compiler on ${ABS_FIL}"
    VERBATIM )
endif(${CMAKE_VERSION} VERSION_GREATER "3.3.2")

add_library(veles_network
    ${INCLUDE_DIR}/network/server.h
    ${PROTO_SRCS}
    ${SRC_DIR}/network/server.cc
    ${PROTO_HDRS}
# python file will only be build if something depends on it
    ${PROTO_PY}
)

add_custom_command(TARGET veles_network POST_BUILD
  COMMENT "Copying generated python file"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
  ${PROTO_PY}
  ${CMAKE_SOURCE_DIR}/python/veles)

add_dependencies(veles_network protobuf)
qt5_use_modules(veles_network Core Network Widgets)

target_link_libraries(veles_network veles_base)
# Windows is too dumb to select correct version on its own
if(WIN32)
  target_link_libraries(veles_network $<$<CONFIG:Debug>:${PROTOBUF_LIBRARY_DEBUG}> $<$<NOT:$<CONFIG:Debug>>:${PROTOBUF_LIBRARY}>)
else(WIN32)
  target_link_libraries(veles_network ${PROTOBUF_LIBRARIES})
endif(WIN32)
