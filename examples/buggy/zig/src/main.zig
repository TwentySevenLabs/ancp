const std = @import("std");
const missing = @import("missing.zig");

pub fn main() void {
    const count: i32 = "bad";
    std.debug.print("{d}", .{missingSymbol});
    takesTwo(1);
}

fn takesTwo(a: i32, b: i32) i32 {
    return a + b;
}

