"""Inspect final Wasm imports without instantiating a guest. Derived from the UlteSoft SDK binary reader."""
HEAPS={0x69:'exn',0x6a:'array',0x6b:'struct',0x6c:'i31',0x6d:'eq',0x6e:'any',
       0x6f:'extern',0x70:'func',0x71:'none',0x72:'noextern',0x73:'nofunc',0x74:'noexn'}
VALUES={0x7f:'i32',0x7e:'i64',0x7d:'f32',0x7c:'f64',0x7b:'v128',0x70:'funcref',0x6f:'externref'}


class Reader:
    """Consume a bounded section; reject truncated fields before advancing."""
    def __init__(self,data):
        self.data=memoryview(data);self.position=0

    def take(self,size):
        """Return exactly size bytes without reading outside this section."""
        if size<0 or size>len(self.data)-self.position:raise ValueError('truncated Wasm field')
        result=self.data[self.position:self.position+size];self.position+=size;return result

    def byte(self):
        """Read one byte; a missing byte is never interpreted as zero."""
        return self.take(1)[0]

    def uint(self,bits=32):
        """Read a width-bounded unsigned LEB field, including legal padding."""
        value=0
        for index in range((bits+6)//7):
            part=self.byte();value|=(part&127)<<(index*7)
            if not part&128:
                if value>=1<<bits:raise ValueError('Wasm LEB value exceeds its width')
                return value
        raise ValueError('unterminated/overwide Wasm LEB field')

    def count(self):
        """Read a vector count bounded by remaining bytes and work budget."""
        result=self.uint()
        if result>100000 or result>len(self.data)-self.position:
            raise ValueError('Wasm vector exceeds section/work bound')
        return result

    def name(self):
        """Decode an exact UTF-8 module/field name with a bounded byte length."""
        return bytes(self.take(self.uint())).decode('utf-8','strict')

    def sint(self,bits=33):
        """Read a signed width-bounded LEB, retaining legal padded sign extension."""
        value=0
        for index in range((bits+6)//7):
            part=self.byte();value|=(part&127)<<(index*7)
            if not part&128:
                if part&64:value-=1<<((index+1)*7)
                if not -(1<<(bits-1))<=value<(1<<(bits-1)):
                    raise ValueError('signed Wasm LEB value exceeds its width')
                return value
        raise ValueError('unterminated/overwide signed Wasm LEB field')

    def value(self,first=None):
        """Read numeric/GC reference syntax; keep references distinct from numbers.

        Heap indices can be forward references within a recursive group. Their
        actual validity/subtyping remains the full validator's responsibility.
        No GC/reference type can become an i32/i64 ROS argument by inspection.
        """
        value=self.byte() if first is None else first
        if value in VALUES:return VALUES[value]
        if value in HEAPS:return 'ref null '+HEAPS[value]
        if value in (0x63,0x64):
            heap=self.sint(33)
            if heap<0:
                if heap+128 not in HEAPS:raise ValueError('unknown abstract Wasm heap type')
                label=HEAPS[heap+128]
            else:label='#'+str(heap)
            return ('ref null ' if value==0x63 else 'ref ')+label
        raise ValueError('advanced Wasm value type is unsupported by this inspector')

    def field(self):
        """Consume one struct/array storage field, including packed i8/i16."""
        value=self.byte()
        if value not in (0x77,0x78):self.value(value)
        if self.byte()>1:raise ValueError('invalid Wasm field mutability')

    def subtype(self,first=None):
        """Return an exact function signature or None for a non-function type.

        Follow the WebAssembly 3.0 binary type grammar, not a scan for 0x60.
        https://webassembly.github.io/spec/core/binary/types.html
        Shared-type/continuation and future type extensions refuse explicitly.
        """
        kind=self.byte() if first is None else first
        if kind in (0x4f,0x50):
            for _ in range(self.count()):self.uint()
            kind=self.byte()
        if kind==0x60:
            params=[self.value() for _ in range(self.count())]
            results=[self.value() for _ in range(self.count())]
            return params,results
        if kind==0x5f:
            for _ in range(self.count()):self.field()
            return None
        if kind==0x5e:self.field();return None
        raise ValueError('unsupported Wasm composite/subtype encoding')

    def types(self):
        """Flatten recursive groups without dropping struct/array index slots.

        Expanded indices share a 100000-entry bound across all groups. This
        is a one-pass bounded syntax reader, never a recursive type expander.
        """
        result=[]
        for _ in range(self.count()):
            kind=self.byte()
            if kind==0x4e:
                count=self.count()
                if count>100000-len(result):raise ValueError('expanded Wasm type budget exceeded')
                for _ in range(count):result.append(self.subtype())
            else:
                if len(result)>=100000:raise ValueError('expanded Wasm type budget exceeded')
                result.append(self.subtype(kind))
        return result

    def limits(self):
        """Consume common 32/64-bit limits; custom-page-size encodings refuse."""
        flags=self.uint()
        if flags&~7:raise ValueError('unsupported Wasm limits flags')
        bits=64 if flags&4 else 32
        self.uint(bits)
        if flags&1:self.uint(bits)

    def end(self):
        """Require complete consumption of a parsed section."""
        if self.position!=len(self.data):raise ValueError('trailing bytes in parsed Wasm section')


def inspect(data):
    """Return function imports and their actual type-section signatures."""
    source=Reader(data)
    if bytes(source.take(8))!=b'\0asm\1\0\0\0':raise ValueError('expected a core Wasm v1 binary')
    types=[];imports=[];seen=set()
    while source.position<len(source.data):
        section=source.byte();body=Reader(source.take(source.uint()))
        if section in (1,2):
            if section in seen:raise ValueError('duplicate type/import section')
            seen.add(section)
        if section==1:
            types=body.types()
            body.end()
        elif section==2:
            for _ in range(body.count()):
                module,name,kind=body.name(),body.name(),body.byte()
                row={'module':module,'name':name,'kind':kind}
                if kind==0:
                    index=body.uint()
                    if index>=len(types) or types[index] is None:
                        raise ValueError('function import type index is not an available function type')
                    row.update(params=types[index][0],results=types[index][1])
                elif kind==1:body.value();body.limits()
                elif kind==2:body.limits()
                elif kind==3:
                    body.value()
                    if body.byte()>1:raise ValueError('invalid global mutability')
                elif kind==4:
                    if body.byte()!=0:raise ValueError('unknown tag attribute')
                    index=body.uint()
                    if index>=len(types) or types[index] is None:
                        raise ValueError('tag type index is not an available function type')
                else:raise ValueError('unknown Wasm import kind')
                imports.append(row)
            body.end()
    return imports


