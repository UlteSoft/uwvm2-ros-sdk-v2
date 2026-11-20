/** @file mitt_harness.ts
 * @brief Execute the assertion surface used by the pinned mitt tests.
 */
type Callback = () => unknown;
const groups: {name: string; setup: Callback[]}[] = [];
const history = new WeakMap<(...values: unknown[]) => void, unknown[][]>();
let current = "";
let totalTests = 0;
let totalAssertions = 0;

export function describe(name: string, body: Callback): void {
  groups.push({name, setup: []});
  try { body(); } finally { groups.pop(); }
}

export function beforeEach(body: Callback): void {
  groups[groups.length - 1].setup.push(body);
}

export function it(name: string, body: Callback): void {
  current = groups.map(group => group.name).concat(name).join(" / ");
  const before = totalAssertions;
  for (const group of groups) for (const setup of group.setup) setup();
  body();
  if (totalAssertions <= before) throw new Error("missing assertion in " + current);
  totalTests++;
}

export function spy() {
  const calls: unknown[][] = [];
  const record = (...values: unknown[]) => { calls.push(values); };
  history.set(record, calls);
  return Object.assign(record, {resetHistory() { calls.length = 0; }});
}

function deepEqual(left: unknown, right: unknown): boolean {
  if (Object.is(left, right)) return true;
  if (Array.isArray(left) && Array.isArray(right)) {
    return left.length === right.length && left.every((item, index) => deepEqual(item, right[index]));
  }
  if (left === null || right === null || typeof left !== "object" || typeof right !== "object") {
    return false;
  }
  if (Object.getPrototypeOf(left) !== Object.prototype || Object.getPrototypeOf(right) !== Object.prototype) {
    return false;
  }
  const l = left as Record<string, unknown>;
  const r = right as Record<string, unknown>;
  const names = Object.keys(l);
  return names.length === Object.keys(r).length &&
    names.every(name => Object.hasOwn(r, name) && deepEqual(l[name], r[name]));
}

class Check {
  constructor(private value: unknown, private inverse = false, private recursive = false) {}
  private test(condition: boolean, message: string): this {
    if (condition === this.inverse) throw new Error(current + " / " + message);
    totalAssertions++;
    return this;
  }
  get to() { return this; }
  get be() { return this; }
  get have() { return this; }
  get been() { return this; }
  get that() { return this; }
  get is() { return this; }
  get and() { return this; }
  get deep() { return new Check(this.value, this.inverse, true); }
  get not() { return new Check(this.value, !this.inverse, this.recursive); }
  get empty() { return this.test(Array.isArray(this.value) && this.value.length === 0, "empty list"); }
  get throw() {
    if (typeof this.value !== "function") throw new Error("expected a callable");
    let thrown = false;
    try { this.value(); } catch { thrown = true; }
    return this.test(thrown, "exception");
  }
  equal(value: unknown) {
    return this.test(this.recursive ? deepEqual(this.value, value) : this.value === value, "equality");
  }
  a(type: string) {
    return this.test(type === "map" ? this.value instanceof Map : typeof this.value === type, "type " + type);
  }
  an(type: string) { return this.a(type); }
  property(name: string) {
    const target = this.value as Record<string, unknown>;
    this.test(target !== null && typeof target === "object" && name in target, "property " + name);
    return new Check(target[name]);
  }
  lengthOf(size: number) {
    return this.test(Array.isArray(this.value) && this.value.length === size, "list length");
  }
  length(size: number) { return this.lengthOf(size); }
  private calls(): unknown[][] {
    if (typeof this.value !== "function") throw new Error("expected a spy");
    const calls = history.get(this.value as (...values: unknown[]) => void);
    if (!calls) throw new Error("unexpected callback");
    return calls;
  }
  get calledOnce() { return this.test(this.calls().length === 1, "one call"); }
  calledWith(...expected: unknown[]) {
    return this.test(this.calls().some(values => values.length >= expected.length &&
      expected.every((value, index) => deepEqual(value, values[index]))), "call arguments");
  }
}

export function expect(value: unknown) { return new Check(value); }

export function verifyTotals(tests: number, assertions: number): void {
  if (totalTests !== tests || totalAssertions !== assertions) {
    throw new Error("unexpected suite totals " + totalTests + " / " + totalAssertions);
  }
}
