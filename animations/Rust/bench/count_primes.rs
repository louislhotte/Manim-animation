// The Rust half of the real benchmark shown in the film.
//
// The SAME algorithm, line for line, as bench/count_primes.py: count primes
// below `limit` by plain trial division. Single thread, no crates. Times the
// pure function (best of `reps`) and prints JSON. `black_box` stops the
// optimizer from deleting the work. The function is formatted to mirror the
// Python version line for line, because the film shows the two side by side.
use std::env;
use std::hint::black_box;
use std::time::Instant;

fn count_primes(limit: u64) -> u64 {
    let mut count = 0;
    for n in 2..limit {
        let mut is_prime = true;
        let mut d = 2;
        while d * d <= n {
            if n % d == 0 { is_prime = false; break; }
            d += 1;
        }
        if is_prime { count += 1; }
    }
    count
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let limit: u64 = args.get(1).map(|s| s.parse().unwrap()).unwrap_or(1_000_000);
    let reps: u32 = args.get(2).map(|s| s.parse().unwrap()).unwrap_or(3);
    let mut best = f64::INFINITY;
    let mut count = 0;
    for _ in 0..reps {
        let t0 = Instant::now();
        count = count_primes(black_box(limit));
        let dt = t0.elapsed().as_secs_f64();
        if dt < best {
            best = dt;
        }
    }
    println!("{{\"count\": {}, \"best_s\": {}}}", black_box(count), best);
}
