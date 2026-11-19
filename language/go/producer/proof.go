// WROS exports the optimized Go SSA directly from its official compiler.
package ssa

import (
	"cmd/compile/internal/ir"
	"encoding/json"
	"fmt"
	"os"
)

type wrosValue struct {
	ID      int    `json:"id"`
	Op      string `json:"op"`
	Type    string `json:"type"`
	Literal int64  `json:"literal,omitempty"`
	Index   int    `json:"index,omitempty"`
	Args    []int  `json:"args,omitempty"`
}

type wrosEdge struct {
	Block int `json:"block"`
	Index int `json:"index"`
}

type wrosBlock struct {
	ID       int         `json:"id"`
	Kind     string      `json:"kind"`
	Control  int         `json:"control,omitempty"`
	Succs    []wrosEdge  `json:"succs,omitempty"`
	PredSize int         `json:"predecessors"`
	Values   []wrosValue `json:"values"`
}

// @brief Export a bounded scalar SSA graph with exact parameter and edge identities.
// @param f Function after the official Go compiler's generic optimization pass.
// @details The encoder independently checks every exported operation and the
// unchanged memory token. Unsupported effects prevent publication of the guest.
func wrosWriteRegisters(f *Func) {
	reject := func(message string) {
		fmt.Fprintf(os.Stderr, "wrgo: function %s is outside the register-only profile: %s\n", f.Name, message)
		os.Exit(2)
	}
	params := f.Type.Params()
	results := f.Type.Results()
	if len(params) > 32 || len(results) != 1 || len(f.Blocks) > 64 {
		reject("signature or block limit")
	}
	types := make([]string, len(params))
	for i, p := range params {
		types[i] = p.Type.String()
	}
	blocks := make([]wrosBlock, 0, len(f.Blocks))
	total := 0
	for _, b := range f.Blocks {
		var controls, successors int
		switch b.Kind {
		case BlockRet:
			controls = 1
		case BlockIf:
			controls, successors = 1, 2
		case BlockPlain:
			successors = 1
		default:
			reject("unsupported block kind " + b.Kind.String())
		}
		if len(b.Succs) != successors || b.NumControls() != controls || b.Aux != nil || b.AuxInt != 0 {
			reject("invalid scalar control flow")
		}
		total += len(b.Values)
		if total > 1024 {
			reject("instruction limit")
		}
		block := wrosBlock{ID: int(b.ID), Kind: b.Kind.String(), PredSize: len(b.Preds),
			Values: make([]wrosValue, 0, len(b.Values))}
		if controls != 0 {
			block.Control = int(b.Controls[0].ID)
		}
		for _, edge := range b.Succs {
			block.Succs = append(block.Succs, wrosEdge{int(edge.Block().ID), edge.Index()})
		}
		for _, v := range b.Values {
			s := wrosValue{ID: int(v.ID), Op: v.Op.String(), Type: v.Type.String(), Literal: v.AuxInt}
			if v.Op == OpArg {
				n, ok := v.Aux.(*ir.Name)
				if !ok {
					reject("invalid parameter origin")
				}
				s.Index = -1
				for i, p := range params {
					if p.Nname == n {
						s.Index = i
						break
					}
				}
				if s.Index < 0 || v.AuxInt != 0 {
					reject("indirect parameter")
				}
			} else if v.Aux != nil {
				reject("requires a symbol, memory reference or runtime operation")
			}
			for _, a := range v.Args {
				s.Args = append(s.Args, int(a.ID))
			}
			block.Values = append(block.Values, s)
		}
		blocks = append(blocks, block)
	}
	result := struct {
		Name   string      `json:"name"`
		Params []string    `json:"params"`
		Result string      `json:"result"`
		Entry  int         `json:"entry"`
		Blocks []wrosBlock `json:"blocks"`
	}{f.Name, types, results[0].Type.String(), int(f.Entry.ID), blocks}
	out, err := os.OpenFile("compiler.jsonl", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0600)
	if err != nil {
		reject(fmt.Sprint(err))
	}
	err = json.NewEncoder(out).Encode(result)
	if closeErr := out.Close(); err == nil {
		err = closeErr
	}
	if err != nil {
		reject(fmt.Sprint(err))
	}
}
