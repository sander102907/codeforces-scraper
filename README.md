# codeforces-scraper
Scraper of solutions from codeforces competitions.

This scraper can fetch problem data and ACCEPTED solutions from all passed competitions on codeforces.
#### The problem data contains:
- Contest ID
- Problem index (e.g. A, B, C ...)
- Problem description
- Example tests (Given when trying to solve the problem)
- All tests (that the solution will be checked against)

#### The solutions data contains:
- Contest ID
- Solution ID (or Submission ID)
- Problem index
- Programming language
- Solution Code

## Methods
There are several methods that can be used to collect the data.

### get_solutions_metadata
This method will fetch solutions metadata of all accepted solutions of passed competitions via the codeforces API.
Metadata contains all the data of the solutions except the actual code. The data will be stored in the folder
```data/contests_solutions_metadata```.
The data will be written to CSV format and a new file will be created every 200 competitions to limit memory usage.

The function can be called by running the script with argument get_solutions_metadata as follows: \
```python main.py get_solutions_metadata```

### get_solutions
This method will fetch the solution source code of the solutions in the solutions metadata files. Hence, before running this method, first run get_solutions_metadata.
The data will be stored in the folder: ```data/contests_solutions_code/{contest_id}/```. So for each contest, a sub-directory will be created containing txt files
of all the solutions from that competition. This script takes extremely long to fetch all millions of solutions, hence you can stop and rerun this method and it will
simply continue from the competitions not yet collected. 

The function can be called by running the script with argument get_solutions as follows: \
```python main.py get_solutions```

By default this will use 40 threads to speed up the collection process, the number of threads can also be specified as follows:

```python main.py get_solutions nr_threads```

### get_problems_data
This method will fetch problem data of all passed competitions, the problem data that is fetched is specified at the start of this readme.
Before running this method, first run get_solutions_metadata.
The data will be stored as ```data/contests_problems/problems_data.csv```

The function can be called by running the script with argument get_problems_data as follows: \
```python main.py get_problems_data```


### merge_solutions_metadata_code
After fetching solutions metadata and solutions code, this method can be used to merge the metadata and source code to a single CSV file.
The data will be stored at ```data/contests_solutions/```

The function can be called by running the script with argument merge_solutions_metadata_code as follows: \
```python main.py merge_solutions_metadata_code```
