/* Freestanding test observer. An old pointer is observed only as a value.
   Actual memory accesses below use the currently live generation. */
typedef __UINTPTR_TYPE__ word;
extern void loop(void **saved, unsigned count);
extern void join(_Bool side);
extern void early(void);
extern void many(void);
extern void mixed(_Bool another);

static unsigned observations, phase, generations, object_differences, last_index;
static word previous, first_object, issued;
static unsigned mixed_differences, observed_nearby, enabled_for_run;
static word observed_address[257], observed_tag[257];
static void *saved;

static void require(_Bool ok) {
  if (!ok)
    __builtin_trap();
}
static word tag(void *p) { return __builtin_wasm_memtag_extract(0, p); }
static void verify_live(void *p) {
  require(tag(p) == tag(__builtin_wasm_memtag_load(0, p)));
  *(volatile unsigned char *)p = 42;
  require(*(volatile unsigned char *)p == 42);
}
void pair(void *prior, void *current) {
  if (phase >= 3) {
    require(issued == (word)prior);
    verify_live(current);
    if (phase == 3)
      require((word)prior == (word)current);
    else if (tag(prior) != tag(current))
      ++mixed_differences;
    ++observations;
    return;
  }
  require((word)prior == previous);
  verify_live(current);
  if (prior && tag(prior) != tag(current))
    ++generations;
  previous = (word)current;
  ++observations;
}
void observe(void *p) {
  if (phase >= 3) {
    if (observations == 0) issued = (word)p;
    else {
      require(issued == (word)p);
      verify_live(p);
    }
  } else if (phase == 1) {
    if ((observations & 1) == 0) issued = (word)p;
    else {
      verify_live(p);
      require(issued == (word)p);
    }
  } else {
    verify_live(p);
    if (observations == 0) issued = (word)p;
    else require(issued == (word)p);
  }
  ++observations;
}
void record(unsigned index, void *p) {
  verify_live(p);
  require(index <= last_index);
  word address = (word)__builtin_wasm_memtag_untag(0, p);
  word color = tag(p);
  if (index == 0) observed_nearby = 0;
  for (unsigned i = 0; i != index; ++i) {
    word other = observed_address[i];
    word distance = address < other ? other - address : address - other;
    require(distance >= 16);
    if (distance <= 80) {
      ++observed_nearby;
      if (enabled_for_run) require(color != observed_tag[i]);
    }
  }
  observed_address[index] = address;
  observed_tag[index] = color;
  if (index == last_index) require(observed_nearby >= last_index);
  if (index == 0) first_object = tag(p);
  if (index == last_index && first_object != tag(p))
    ++object_differences;
  ++observations;
}
void check_stack_generations(unsigned enabled) {
  require((__builtin_wasm_memtag_status(0) != 0) == enabled);
  enabled_for_run = enabled;
  last_index = sizeof(word) == 4 ? 16 : 256;
  loop(&saved, 128);
  require(observations == 128);
  phase = 1;
  observations = 0;
  early();
  require(observations == 4);
  phase = 2;
  for (unsigned side = 0; side <= 1; ++side) {
    observations = 0;
    join(side);
    require(observations == 2);
  }
  for (unsigned side = 0; side <= 1; ++side) {
    phase = 3 + side;
    for (unsigned i = 0; i != 64; ++i) {
      observations = 0;
      mixed(side);
      require(observations == 2 + side);
    }
  }
  observations = 0;
  for (unsigned i = 0; i != 64; ++i) many();
  require(observations == (last_index + 1) * 64);
  if (enabled) {
    require(generations != 0);
    require(object_differences != 0 && mixed_differences != 0);
  } else {
    require(generations == 0 && object_differences == 0 && mixed_differences == 0);
  }
}
