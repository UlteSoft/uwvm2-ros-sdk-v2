/** @file twist.cpp
 *  @brief Emit the genuine ROS 2 Fast RTPS CDR1 encoding of geometry_msgs/Twist for the migration fixture.
 */
#include <array>
#include <cstdio>
#include <fastcdr/Cdr.h>
#include <fastcdr/FastBuffer.h>
#include <geometry_msgs/msg/detail/twist__rosidl_typesupport_fastrtps_cpp.hpp>

int main()
{
    geometry_msgs::msg::Twist twist;
    twist.linear.x = 1.0;
    twist.linear.y = -2.0;
    twist.linear.z = 3.5;
    twist.angular.x = 0.5;
    twist.angular.y = 0.0;
    twist.angular.z = -2.5;
    std::array<char, 64> bytes{};
    eprosima::fastcdr::FastBuffer buffer(bytes.data(), bytes.size());
    eprosima::fastcdr::Cdr writer(buffer, eprosima::fastcdr::Cdr::LITTLE_ENDIANNESS, eprosima::fastcdr::CdrVersion::XCDRv1);
    writer.serialize_encapsulation();
    if (!geometry_msgs::msg::typesupport_fastrtps_cpp::cdr_serialize(twist, writer))
        return 1;
    return std::fwrite(bytes.data(), 1, writer.get_serialized_data_length(), stdout) == 52 ? 0 : 1;
}
