import { wr_abi } from "uwrosv2/capability";
if (wr_abi() !== 2) throw Error("expected ROS ABI 2");
