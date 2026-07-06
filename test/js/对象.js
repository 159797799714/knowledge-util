
let person = {
    name: '张三',
    age: 18,
    sex: '男',
    run: function(){
        console.log(this.name + ' is running...')
    }
}


person.run()

console.dir(person)


person.score = 100

console.dir(person)

person.eat = function(){
    console.log(this.name + ' is eating...')
}

person.eat()