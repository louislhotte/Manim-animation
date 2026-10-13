fn main() {
    let mut v = vec![1, 2, 3];
    let first = &v[0];
    v.push(4);
    println!("{first}");
}
// Mutate-while-borrowed demo. rustc's REAL error (E0502): `push` may reallocate
// the buffer, which would leave `first` dangling. Shown verbatim in the film.
