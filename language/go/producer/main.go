// Copyright 2015 The Go Authors. All rights reserved.
// Use of this source code is governed by the BSD-style license in LICENSE.
// WROS builds this entry point in the Go release's cmd/compile package.
package main

import (
	"cmd/compile/internal/base"
	"cmd/compile/internal/gc"
	"cmd/compile/internal/wasm"
	"go/ast"
	"go/parser"
	"go/token"
	"internal/buildcfg"
	"log"
	"os"
	"regexp"
	"strings"
)

// @brief Compile one bounded Go source using the fixed Wasm backend.
// @details The SDK receives optimized scalar SSA through the proof hook.
// Imports, runtime link directives, and native target selection are rejected.
func main() {
	log.SetFlags(0)
	log.SetPrefix("wrgo: ")
	if buildcfg.GOARCH != "wasm" || buildcfg.GOOS != "wasip1" || len(os.Args) != 1 {
		log.Fatal("expected the SDK's fixed wasm32-wasip1 compiler invocation")
	}
	body, err := os.ReadFile("input.go")
	if err != nil || len(body) == 0 || len(body) > 1<<20 {
		log.Fatal("expected one Go source file of at most 1 MiB")
	}
	source, err := parser.ParseFile(token.NewFileSet(), "input.go", body, parser.ParseComments)
	if err != nil {
		log.Fatal(err)
	}
	for _, group := range source.Comments {
		for _, comment := range group.List {
			if strings.HasPrefix(comment.Text, "//go:") || strings.HasPrefix(comment.Text, "//line ") || strings.HasPrefix(comment.Text, "/*line ") {
				log.Fatal("compiler and line directives are outside the register-only profile")
			}
		}
	}
	if len(source.Decls) == 0 || len(source.Decls) > 128 {
		log.Fatal("expected 1 to 128 top-level scalar functions")
	}
	identifier := regexp.MustCompile("^[A-Za-z][A-Za-z0-9_]{0,63}$")
	for _, d := range source.Decls {
		f, ok := d.(*ast.FuncDecl)
		if !ok || f.Body == nil || f.Recv != nil || f.Type.TypeParams != nil || !identifier.MatchString(f.Name.Name) || f.Name.Name == "init" || f.Name.Name == "main" {
			log.Fatal("expected scalar function definitions without imports, methods, package initialization, or package state")
		}
	}
	os.Args = []string{"wrgo", "-c=1", "-p=wrosguest", "-o=discard.o", "input.go"}
	gc.Main(wasm.Init)
	base.Exit(0)
}
