class Test():
    count = 0
    def func(self):
        self.count += 1
        print self.count

x = Test()
y = Test()
x.func()
x.func()
x.func()

y.func()
abc