console.log(typeof '123')
console.log(typeof 123)
console.log(typeof true)
console.log(typeof 'abc')
console.log(typeof alert)
console.log(typeof new Date())
console.log(typeof {name: "zhangsan", age: 18})

let a
console.log(typeof a)

let name = document.getElementById("name")

console.log(typeof name)
console.log(name)


// let cars=new Array();
// cars[0]="Saab";
// cars[1]="Volvo";
// cars[2]="BMW";
// let cars=new Array("Saab","Volvo","BMW");
let cars = ["Saab", "Volvo", "BMW"];
console.dir(cars)
console.log(cars)


let person = {
    firstname: "John",
    lastname: "Doe",
    id: 5566
};

let aaa = "id"
name=person.lastname;
name=person[aaa];