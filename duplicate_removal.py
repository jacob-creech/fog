queue_file = open('queue.txt', 'r')
queue_file_fixed = open('queue_fixed.txt', 'w')
unique_id = []
count = 1
cycle_size = int(raw_input('Enter the cycle size: '))
for line in queue_file:
    adjusted_line = line[:17]
    if adjusted_line not in unique_id:
        unique_id += [adjusted_line]
        queue_file_fixed.write(adjusted_line + '\n')
    if count % cycle_size == 0:
        print adjusted_line, count
        queue_file_fixed.close()
        queue_file_fixed = open('queue_fixed.txt', 'a')
        unique_id = []
    count += 1
queue_file.close()
queue_file_fixed.close()