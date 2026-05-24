<?php
require "missing.php";

$count = "bad";
echo $missingSymbol;

function takesTwo(int $a, int $b): int {
    return $a + $b;
}

takesTwo(1);

if (true) {
    echo "missing brace";

