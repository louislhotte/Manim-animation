fn main() {
    let s = String::from("hello");
    let t = s;
    println!("{s}");
}
// Use-after-move demo. The film shows rustc's REAL error for this file (E0382).
// (`t` is deliberately unused; compilation aborts before the lint would fire.)
