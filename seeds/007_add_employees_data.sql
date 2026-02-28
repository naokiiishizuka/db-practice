INSERT INTO employees (employee_code, name, department, salary, hire_date)
VALUES
  ('ENG-A1', 'Alice', 'Engineering', 9000000, '2021-05-01'),
  ('ENG-B2', 'Bob', 'Engineering', 7500000, '2022-01-15'),
  ('MKT-C3', 'Carol', 'Marketing', 6400000, '2020-11-20'),
  ('MKT-D4', 'Dave', 'Marketing', 7200000, '2023-07-10'),
  ('SAL-E5', 'Eve', 'Sales', 6800000, '2021-03-05'),
  ('SAL-F6', 'Frank', 'Sales', 5500000, '2022-09-18')
ON CONFLICT (employee_code) DO NOTHING;
