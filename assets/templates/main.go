package main

import (
	"bufio"
	"fmt"
	"os"
)

func main() {
	sc := bufio.NewScanner(os.Stdin)
	sc.Split(bufio.ScanWords)
	if !sc.Scan() {
		return
	}
	fmt.Println(sc.Text())
}
