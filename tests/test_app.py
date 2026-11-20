import unittest

from app import create_app


class EmployeeApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "TESTING": True,
        })
        self.client = self.app.test_client()

    def login(self):
        return self.client.post("/login", data={"username": "admin", "password": "admin123"})

    def payload(self, **kw):
        data = {"firstName": "Asha", "lastName": "Rao", "email": "asha@example.com",
                "phone": "9876543210", "salary": 55000, "hireDate": "2024-01-15",
                "departmentId": 1}
        data.update(kw)
        return data

    def test_api_requires_login(self):
        self.assertEqual(self.client.get("/api/employees").status_code, 401)

    def test_bad_login(self):
        res = self.client.post("/login", data={"username": "admin", "password": "wrong"})
        self.assertIn(b"Invalid username or password", res.data)

    def test_crud_and_search(self):
        self.login()
        res = self.client.post("/api/employees", json=self.payload())
        self.assertEqual(res.status_code, 201)
        emp_id = res.get_json()["id"]

        self.assertEqual(self.client.post("/api/employees", json=self.payload()).status_code, 400)

        res = self.client.put(f"/api/employees/{emp_id}", json=self.payload(salary=60000))
        self.assertEqual(res.get_json()["salary"], 60000.0)

        self.assertEqual(len(self.client.get("/api/employees?search=asha").get_json()), 1)
        self.assertEqual(len(self.client.get("/api/employees?search=zzz").get_json()), 0)

        stats = self.client.get("/api/employees/stats").get_json()
        self.assertEqual(stats["totalEmployees"], 1)
        self.assertEqual(stats["totalPayroll"], 60000.0)

        self.assertEqual(self.client.delete(f"/api/employees/{emp_id}").status_code, 204)
        self.assertEqual(self.client.get(f"/api/employees/{emp_id}").status_code, 404)

    def test_validation(self):
        self.login()
        res = self.client.post("/api/employees", json=self.payload(email="bad"))
        self.assertEqual(res.status_code, 400)
        res = self.client.post("/api/employees", json=self.payload(salary=-5))
        self.assertEqual(res.status_code, 400)

    def test_department_rules(self):
        self.login()
        self.client.post("/api/employees", json=self.payload())
        self.assertEqual(self.client.delete("/api/departments/1").status_code, 400)
        res = self.client.post("/api/departments", json={"name": "Legal"})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(self.client.delete(f"/api/departments/{res.get_json()['id']}").status_code, 204)


if __name__ == "__main__":
    unittest.main()
