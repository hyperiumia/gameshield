-- Bounded FIFO with drop-oldest policy: memory stays fixed under load.
local Queue = {}
Queue.__index = Queue

function Queue.new(max)
    return setmetatable({ items = {}, head = 1, tail = 0, max = max or 10000 }, Queue)
end

function Queue:count()
    return self.tail - self.head + 1
end

function Queue:push(item)
    self.tail = self.tail + 1
    self.items[self.tail] = item
    if self:count() > self.max then
        self.items[self.head] = nil
        self.head = self.head + 1
    end
end

function Queue:pop_many(n)
    local out = {}
    for _ = 1, math.min(n, self:count()) do
        out[#out + 1] = self.items[self.head]
        self.items[self.head] = nil
        self.head = self.head + 1
    end
    if self:count() == 0 then
        self.head, self.tail = 1, 0
    end
    return out
end

return Queue
