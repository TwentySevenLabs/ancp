fn main() {
    let name: i32 = "not a number";
    println!("{}", missing_value);
    takes_two_args(1);
    let moved = String::from("hello");
    let other = moved;
    println!("{}", moved);
}

fn takes_two_args(a: i32, b: i32) -> i32 {
    a + b
}

