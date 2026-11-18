/** @file Verify paired service readiness using the installed C SDK and two provisioned ROS 2 peers. */
#include <stdint.h>
#include <string.h>
#include <wros/scene.h>
#include "worker_profiles.h"

typedef uint32_t operation(uint64_t,uint32_t,uint64_t,uint64_t,uint64_t,uint64_t,uint64_t);
struct client {
    uint64_t context_cap, context, node_cap, node_request, node, service_cap, service_request, endpoint;
    uint64_t request_schema, response_schema;
};
static struct client peers[2];
static uint8_t request[1024];
static uint64_t response[16], used, clock_cap, clock_id, limit;
static size_t size;

static void check(int ok) { if(!ok) __builtin_trap(); }
static uint64_t address(void const *value) { return (uintptr_t)value; }
static void put(void const *body, size_t n) {
    check(n<=sizeof(request)-size);
    memcpy(request+size,body,n);
    size+=n;
}
static void word(uint64_t n) { put(&n,sizeof(n)); }
static uint64_t open_grant(char const *name) {
    uint64_t value=0;
    check(wr_capability_open(0,address(name),strlen(name),address(&value))==0 && value);
    return value;
}
static uint32_t invoke(operation *fn,uint64_t cap,uint64_t capacity) {
    used=0;
    memset(response,0,sizeof(response));
    return fn(cap,0,address(request),size,address(response),capacity,address(&used));
}
static uint64_t steady(void) {
    uint64_t time[4], bytes=0;
    check(wr_clock_read(clock_cap,0,address(&clock_id),8,address(time),sizeof(time),address(&bytes))==0 && bytes>=8);
    return time[0];
}
static void poll(operation *fn,uint64_t cap) {
    uint32_t status;
    do {status=invoke(fn,cap,sizeof(response));check(status==0||status==11);check(steady()<limit);} while (status);
}
static void take(uint64_t cap,uint64_t receipt,unsigned kind,uint64_t *value) {
    size=0;word(receipt);poll(wr_communication_open_take,cap);
    check(used==64 && response[6]==kind && response[7]!=0);
    *value=response[7];
}
void _start(void) {
    check(wr_abi()==2);
    clock_cap=open_grant("steady");size=0;word(0);
    check(invoke(wr_clock_create,clock_cap,8)==0);clock_id=response[0];limit=steady()+60000000000ull;
    uint64_t observer=open_grant("observe-client");
    for(unsigned i=0;i<2;++i) {
        struct client *p=&peers[i];
        p->context_cap=open_grant(profiles[i].context_alias);
        p->node_cap=open_grant(profiles[i].node_alias);
        p->service_cap=open_grant(profiles[i].service_alias);
        p->request_schema=open_grant(profiles[i].request_alias);p->response_schema=open_grant(profiles[i].response_alias);
        size=0;put(profiles[i].context,profiles[i].context_bytes);
        check(invoke(wr_context_open,p->context_cap,8)==0 && used==8);p->context=response[0];
        size=0;word(p->context_cap);word(p->context);put(profiles[i].node,profiles[i].node_bytes);
        word(1);word(steady()+14000000000ull);
        check(invoke(wr_node_open,p->node_cap,48)==0 && used==48);p->node_request=response[1];
    }
    for(unsigned i=0;i<2;++i) {
        struct client *p=&peers[i];
        take(p->node_cap,p->node_request,1,&p->node);
        size=0;word(p->node_cap);word(p->node);word(2);word(p->request_schema);word(p->response_schema);
        put(profiles[i].service,profiles[i].service_bytes);word(1);word(steady()+900000000ull);
        check(invoke(wr_service_open,p->service_cap,48)==0 && used==48);p->service_request=response[1];
    }
    for(unsigned i=0;i<2;++i)take(peers[i].service_cap,peers[i].service_request,3,&peers[i].endpoint);
    size=0;word(peers[0].endpoint);check(invoke(wr_service_available,observer,32)==22);
    word(0);check(invoke(wr_service_available,observer,32)==13);
    size=8;word(peers[1].service_cap);check(invoke(wr_service_available,observer,32)==13);
    size=8;word(peers[0].service_cap);check(invoke(wr_service_available,peers[0].service_cap,32)==13);
    check(invoke(wr_service_available,observer,31)==90 && used==32);
    do {poll(wr_service_available,observer);check(used==32 && response[0]<=1);} while(!response[0]);
    for(unsigned i=0;i<2;++i) {
        size=0;word(peers[i].endpoint);poll(wr_resource_close,peers[i].service_cap);
        size=0;word(peers[i].service_request);poll(wr_request_release,peers[i].service_cap);
    }
    for(unsigned i=0;i<2;++i) {size=0;word(peers[i].node);poll(wr_resource_close,peers[i].node_cap);}
}
