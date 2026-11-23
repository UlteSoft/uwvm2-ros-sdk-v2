// Code generated from Unitree ROS 2 v0.3.0 .msg files by generate_go.py. DO NOT EDIT.

// Package unitreeapi maps the public unitree_api message definitions to Go.
package unitreeapi

// Request represents unitree_api/msg/Request.
type Request struct {
	Header    RequestHeader `json:"header"`
	Parameter string        `json:"parameter"`
	Binary    []uint8       `json:"binary"`
}

// RequestHeader represents unitree_api/msg/RequestHeader.
type RequestHeader struct {
	Identity RequestIdentity `json:"identity"`
	Lease    RequestLease    `json:"lease"`
	Policy   RequestPolicy   `json:"policy"`
}

// RequestIdentity represents unitree_api/msg/RequestIdentity.
type RequestIdentity struct {
	ID    int64 `json:"id"`
	APIID int64 `json:"api_id"`
}

// RequestLease represents unitree_api/msg/RequestLease.
type RequestLease struct {
	ID int64 `json:"id"`
}

// RequestPolicy represents unitree_api/msg/RequestPolicy.
type RequestPolicy struct {
	Priority int32 `json:"priority"`
	Noreply  bool  `json:"noreply"`
}

// Response represents unitree_api/msg/Response.
type Response struct {
	Header ResponseHeader `json:"header"`
	Data   string         `json:"data"`
	Binary []int8         `json:"binary"`
}

// ResponseHeader represents unitree_api/msg/ResponseHeader.
type ResponseHeader struct {
	Identity RequestIdentity `json:"identity"`
	Status   ResponseStatus  `json:"status"`
}

// ResponseStatus represents unitree_api/msg/ResponseStatus.
type ResponseStatus struct {
	Code int32 `json:"code"`
}
