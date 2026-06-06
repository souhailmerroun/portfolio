export type Challenge = {
  language: string;
  prompt: string;
  answers: string[];
};

const norm = (s: string) =>
  s.replace(/\s+/g, " ").replace(/\s*([(){}\[\],;:=<>+\-*/])\s*/g, "$1").trim().toLowerCase();

export function isCorrect(input: string, answers: string[]): boolean {
  const n = norm(input);
  return answers.some((a) => norm(a) === n);
}

export const LANGUAGES = [
  "JavaScript",
  "TypeScript",
  "React",
  "Python",
  "PHP",
  "Go",
  "Rust",
  "Java",
  "C#",
  "Ruby",
  "Bash",
  "SQL",
] as const;

export type Language = (typeof LANGUAGES)[number];

export const CHALLENGES: Challenge[] = [
  {
    language: "JavaScript",
    prompt: "Declare a constant named pi with value 3.14",
    answers: ["const pi = 3.14;", "const pi = 3.14"],
  },
  {
    language: "JavaScript",
    prompt: "Write an arrow function add that takes a and b and returns their sum",
    answers: [
      "const add = (a, b) => a + b;",
      "const add = (a, b) => a + b",
      "let add = (a, b) => a + b;",
      "const add = (a,b) => a+b;",
    ],
  },
  {
    language: "JavaScript",
    prompt: "Print 'hello' to the console",
    answers: ["console.log('hello');", "console.log(\"hello\");", "console.log('hello')", "console.log(\"hello\")"],
  },
  {
    language: "JavaScript",
    prompt: "Check if array arr is empty (boolean expression)",
    answers: ["arr.length === 0", "arr.length == 0", "arr.length===0"],
  },
  {
    language: "Python",
    prompt: "Define a function greet that takes name and returns 'Hello ' + name",
    answers: [
      "def greet(name): return 'Hello ' + name",
      "def greet(name): return \"Hello \" + name",
      "def greet(name):\n    return 'Hello ' + name",
    ],
  },
  {
    language: "Python",
    prompt: "Print 'hello' to stdout",
    answers: ["print('hello')", "print(\"hello\")"],
  },
  {
    language: "Python",
    prompt: "Create a list comprehension of squares from 0 to 9 named squares",
    answers: [
      "squares = [x*x for x in range(10)]",
      "squares = [x**2 for x in range(10)]",
      "squares=[x*x for x in range(10)]",
    ],
  },
  {
    language: "Python",
    prompt: "Open file 'data.txt' for reading and assign to f",
    answers: ["f = open('data.txt', 'r')", "f = open(\"data.txt\", \"r\")", "f = open('data.txt','r')"],
  },
  {
    language: "PHP",
    prompt: "Define a function sum that takes $a and $b and returns their sum",
    answers: [
      "function sum($a, $b) { return $a + $b; }",
      "function sum($a,$b){return $a+$b;}",
    ],
  },
  {
    language: "PHP",
    prompt: "Echo 'hello' in PHP",
    answers: ["echo 'hello';", "echo \"hello\";"],
  },
  {
    language: "PHP",
    prompt: "Assign an associative array with key 'name' value 'Bob' to $user",
    answers: [
      "$user = ['name' => 'Bob'];",
      "$user = array('name' => 'Bob');",
      "$user = [\"name\" => \"Bob\"];",
    ],
  },
  {
    language: "Go",
    prompt: "Declare a variable x of type int with value 42",
    answers: ["var x int = 42", "x := 42"],
  },
  {
    language: "Go",
    prompt: "Print 'hello' using fmt",
    answers: ["fmt.Println(\"hello\")", "fmt.Print(\"hello\")"],
  },
  {
    language: "Rust",
    prompt: "Declare an immutable variable x with value 10",
    answers: ["let x = 10;", "let x: i32 = 10;"],
  },
  {
    language: "Rust",
    prompt: "Print 'hello' to stdout",
    answers: ["println!(\"hello\");", "print!(\"hello\");"],
  },
  {
    language: "Java",
    prompt: "Print 'hello' to stdout",
    answers: ["System.out.println(\"hello\");", "System.out.print(\"hello\");"],
  },
  {
    language: "Java",
    prompt: "Declare a final int constant MAX with value 100",
    answers: ["final int MAX = 100;"],
  },
  {
    language: "C#",
    prompt: "Print 'hello' to console",
    answers: ["Console.WriteLine(\"hello\");", "Console.Write(\"hello\");"],
  },
  {
    language: "Ruby",
    prompt: "Print 'hello' to stdout",
    answers: ["puts 'hello'", "puts \"hello\"", "print 'hello'"],
  },
  {
    language: "Ruby",
    prompt: "Define a method greet that takes name and returns \"Hello #{name}\"",
    answers: [
      "def greet(name); \"Hello #{name}\"; end",
      "def greet(name) \"Hello #{name}\" end",
    ],
  },
  {
    language: "TypeScript",
    prompt: "Define a type User with a string field name",
    answers: ["type User = { name: string };", "type User = { name: string }"],
  },
  {
    language: "TypeScript",
    prompt: "Declare an array of numbers named nums with values 1, 2, 3",
    answers: [
      "const nums: number[] = [1, 2, 3];",
      "const nums: Array<number> = [1, 2, 3];",
      "let nums: number[] = [1, 2, 3];",
    ],
  },
  {
    language: "React",
    prompt: "Declare a state variable count initialized to 0 using useState",
    answers: [
      "const [count, setCount] = useState(0);",
      "const [count, setCount] = useState(0)",
    ],
  },
  {
    language: "React",
    prompt: "Return a div with text 'hello' (JSX expression)",
    answers: ["<div>hello</div>", "return <div>hello</div>;", "return <div>hello</div>"],
  },
  {
    language: "React",
    prompt: "Import useEffect from react",
    answers: [
      "import { useEffect } from 'react';",
      "import { useEffect } from \"react\";",
      "import {useEffect} from 'react';",
    ],
  },
  {
    language: "Bash",
    prompt: "Print 'hello' to stdout",
    answers: ["echo hello", "echo 'hello'", "echo \"hello\"", "printf 'hello'"],
  },
  {
    language: "SQL",
    prompt: "Select all columns from table users",
    answers: ["SELECT * FROM users;", "SELECT * FROM users", "select * from users;", "select * from users"],
  },
  {
    language: "SQL",
    prompt: "Count rows in table orders (aliased as total)",
    answers: [
      "SELECT COUNT(*) AS total FROM orders;",
      "SELECT COUNT(*) AS total FROM orders",
    ],
  },
];
