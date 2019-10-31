import os
import queue


down_load_records = {
    1: 0.2,
    2: 1,
    3: 0.5
}



print('%s' % ''.join(list(map(lambda x: str(x), filter(lambda key: down_load_records[key] >= 1, down_load_records)))))
