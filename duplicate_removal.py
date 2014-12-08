cycle_size = int(raw_input('Enter the cycle size: '))
read_file_name = raw_input('Enter the name of the input file: ')
write_file_name = raw_input('Enter the name of the output file: ')
read_file = open(read_file_name, 'r')
write_file = open(write_file_name, 'w')
unique_id = []
count = 1
for line in read_file:
    steam_id = line[:17]
    if steam_id not in unique_id:
        unique_id += [steam_id]
        write_file.write(line)
    if count % cycle_size == 0:
        print steam_id, count
        write_file.close()
        write_file = open(write_file_name, 'a')
        unique_id = []
    count += 1
read_file.close()
write_file.close()