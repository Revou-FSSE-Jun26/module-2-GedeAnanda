# RevoShop API

REST API untuk platform e-commerce RevoShop, dibangun dengan Flask, SQLAlchemy, dan PostgreSQL. API ini mengelola users, categories, products, orders, dan order items melalui interface RESTful dengan autentikasi berbasis JWT dan kontrol akses berbasis role.

**Dokumentasi endpoint lengkap:** [Postman Documentation](https://documenter.getpostman.com/view/49407169/2sBYAuSAwp)

---

## Daftar Isi

- [Overview](#overview)
- [Fitur](#fitur)
- [Teknologi](#teknologi)
- [Struktur Database](#struktur-database)
- [Struktur Project](#struktur-project)
- [Menjalankan Project Secara Lokal](#menjalankan-project-secara-lokal)
- [Daftar Endpoint](#daftar-endpoint)
- [Autentikasi & Otorisasi](#autentikasi--otorisasi)
- [Testing](#testing)
- [Load Testing](#load-testing)
- [Catatan Desain](#catatan-desain)
- [Screenshots](#screenshots)

---

## Overview

RevoShop adalah backend API untuk toko online yang mengelola katalog produk berkategori, akun pengguna, dan pemesanan. Setiap order dapat berisi beberapa produk sekaligus, dan setiap produk dapat muncul di banyak order berbeda — relasi many-to-many yang dijembatani tabel `order_items`, yang juga menyimpan quantity dan harga pada saat transaksi terjadi.

API ini dirancang sebagai sistem toko tunggal: admin mengelola katalog (kategori dan produk), sementara customer melihat katalog dan membuat pesanan.

---

## Fitur

**Autentikasi & Otorisasi**
- Registrasi dan login dengan password ter-hash
- JWT dengan access token (30 menit) dan refresh token (30 hari)
- Logout dengan token revocation melalui blocklist
- Role-based access control (admin / customer)

**Manajemen Katalog**
- CRUD penuh untuk categories dan products
- Pagination, filtering (berdasarkan kategori dan status aktif), dan pencarian nama produk
- Deletion guard: produk yang sudah pernah dipesan tidak dapat dihapus
- Deletion guard: kategori yang masih memiliki produk tidak dapat dihapus

**Manajemen Order**
- Pembuatan order dengan beberapa produk sekaligus
- Perhitungan `total_amount` otomatis
- Pengurangan stock otomatis saat order dibuat
- Validasi ketersediaan stock dan status aktif produk sebelum order diproses
- Penggabungan otomatis item duplikat dalam satu order
- Row-level locking untuk mencegah race condition saat stock diperebutkan
- Pembatalan order dengan pengembalian stock
- Customer hanya dapat melihat ordernya sendiri; admin dapat melihat semua

**Kualitas & Keamanan**
- Validasi input di seluruh endpoint dengan pesan error yang spesifik
- Global error handler: semua error dikembalikan sebagai JSON dengan status code yang tepat
- Rollback otomatis pada kegagalan transaksi database
- Konfigurasi sensitif dipisahkan ke `.env`

---

## Teknologi

| Kategori | Teknologi |
|---|---|
| Framework | Flask |
| ORM | SQLAlchemy (Flask-SQLAlchemy) |
| Migrasi | Flask-Migrate (Alembic) |
| Database | PostgreSQL |
| Autentikasi | Flask-JWT-Extended |
| Konfigurasi | python-dotenv |
| Testing | pytest |
| Load Testing | Locust |
| Database GUI | pgAdmin |

---

## Struktur Database

Lima tabel inti dengan relasi berikut:

- **users** → **orders** (one-to-many): satu user dapat memiliki banyak order
- **categories** → **products** (one-to-many): satu kategori memiliki banyak produk
- **orders** ↔ **products** (many-to-many via **order_items**): satu order berisi banyak produk, satu produk muncul di banyak order

Tabel tambahan **token_blocklist** menyimpan JWT ID (`jti`) dari token yang sudah di-revoke saat logout.

### Aturan Referential Integrity

| Relasi | ON DELETE | Alasan |
|---|---|---|
| `order_items` → `orders` | CASCADE | Item tidak bermakna tanpa ordernya |
| `order_items` → `products` | RESTRICT | Menjaga riwayat transaksi tetap utuh |
| `products` → `categories` | RESTRICT | Mencegah produk kehilangan kategori |
| `orders` → `users` | RESTRICT | Menjaga riwayat order tetap terhubung ke pemiliknya |

Harga produk disalin ke `order_items.price` saat order dibuat, bukan direferensikan. Ini memastikan perubahan harga di masa depan tidak mengubah nilai transaksi yang sudah terjadi.

---

## Struktur Project

```
revoshop-api/
├── app/
│   ├── __init__.py          # application factory
│   ├── config.py            # konfigurasi (Config, TestConfig)
│   ├── extensions.py        # instance db, migrate, jwt
│   ├── models/
│   │   ├── user.py          # User
│   │   ├── product.py       # Category, Product
│   │   ├── order.py         # Order, OrderItem
│   │   └── token.py         # TokenBlocklist
│   ├── routes/
│   │   ├── auth.py          # register, login, refresh, logout, me
│   │   ├── categories.py    # CRUD categories
│   │   ├── products.py      # CRUD products
│   │   └── orders.py        # order, cancel, status
│   └── utils/
│       ├── decorators.py    # role_required
│       └── errors.py        # global error handlers
├── migrations/              # Alembic migration files
├── tests/
│   ├── conftest.py          # fixtures
│   ├── test_auth.py
│   ├── test_categories.py
│   ├── test_products.py
│   └── test_orders.py
├── .env.example
├── .gitignore
├── locustfile.py
├── requirements.txt
└── run.py
```

---

## Menjalankan Project Secara Lokal

### Prasyarat

- Python 3.10+
- PostgreSQL

### 1. Clone repository

```bash
git clone https://github.com/Revou-FSSE-Jun26/module-2-GedeAnanda.git
cd module-2-GedeAnanda
```

### 2. Buat dan aktifkan virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Buat database

Melalui pgAdmin atau psql, buat dua database:

```sql
CREATE DATABASE revoshop_db;
CREATE DATABASE revoshop_test;
```

### 5. Konfigurasi environment

Salin `.env.example` menjadi `.env`, lalu isi nilainya:

```bash
cp .env.example .env
```

```
DATABASE_URL=postgresql://postgres:password@localhost:5432/revoshop_db
TEST_DATABASE_URL=postgresql://postgres:password@localhost:5432/revoshop_test
SECRET_KEY=<string acak>
JWT_SECRET_KEY=<string acak>
```

Generate secret key dengan:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 6. Jalankan migrasi

```bash
export FLASK_APP=run.py          # Windows: set FLASK_APP=run.py
flask db upgrade
```

### 7. Jalankan aplikasi

```bash
flask run
```

API berjalan di `http://127.0.0.1:5000`.

### 8. Membuat akun admin

Endpoint POST, PUT, dan DELETE untuk products dan categories memerlukan role `admin`. Registrasi publik selalu menghasilkan role `customer` — ini disengaja, agar tidak ada jalur untuk self-assign menjadi admin.

Daftarkan user melalui API, lalu promosikan melalui database:

```sql
UPDATE users SET role = 'admin' WHERE email = 'email_anda@example.com';
```

Login ulang setelahnya agar token yang baru membawa role admin.

---

## Daftar Endpoint

Dokumentasi lengkap dengan contoh request dan response tersedia di [Postman Documentation](https://documenter.getpostman.com/view/49407169/2sBYAuSAwp).

### Auth

| Method | Endpoint | Akses | Deskripsi |
|---|---|---|---|
| POST | `/auth/register` | Publik | Registrasi user baru |
| POST | `/auth/login` | Publik | Login, mengembalikan access & refresh token |
| POST | `/auth/refresh` | Refresh token | Menukar refresh token dengan access token baru |
| POST | `/auth/logout` | Terautentikasi | Me-revoke access token saat ini |
| GET | `/auth/me` | Terautentikasi | Data user yang sedang login |

### Categories

| Method | Endpoint | Akses | Deskripsi |
|---|---|---|---|
| GET | `/categories` | Publik | Daftar semua kategori |
| GET | `/categories/<id>` | Publik | Detail kategori beserta produknya |
| POST | `/categories` | Admin | Membuat kategori baru |
| PUT | `/categories/<id>` | Admin | Memperbarui kategori |
| DELETE | `/categories/<id>` | Admin | Menghapus kategori (ditolak jika masih ada produk) |

### Products

| Method | Endpoint | Akses | Deskripsi |
|---|---|---|---|
| GET | `/products` | Publik | Daftar produk dengan pagination, filter, dan pencarian |
| GET | `/products/<id>` | Publik | Detail satu produk |
| POST | `/products` | Admin | Membuat produk baru |
| PUT | `/products/<id>` | Admin | Memperbarui produk |
| DELETE | `/products/<id>` | Admin | Menghapus produk (ditolak jika sudah pernah dipesan) |

Query parameter untuk `GET /products`: `page`, `per_page`, `category_id`, `is_active`, `search`.

### Orders

| Method | Endpoint | Akses | Deskripsi |
|---|---|---|---|
| GET | `/orders` | Terautentikasi | Daftar order milik user (admin melihat semua) |
| GET | `/orders/<id>` | Terautentikasi | Detail order beserta item dan produknya |
| POST | `/orders` | Terautentikasi | Membuat order baru |
| PUT | `/orders/<id>/status` | Admin | Mengubah status order |
| POST | `/orders/<id>/cancel` | Terautentikasi | Membatalkan order dan mengembalikan stock |

Status yang valid: `pending`, `paid`, `shipped`, `completed`, `cancelled`.

### Format Response

Response sukses:

```json
{
  "message": "Products retrieved successfully",
  "data": [ ... ],
  "pagination": { ... }
}
```

Response error:

```json
{
  "error": "Product not found"
}
```

---

## Autentikasi & Otorisasi

API menggunakan JWT dengan pola access token dan refresh token.

**Access token** (30 menit) dikirim pada setiap request yang memerlukan autentikasi:

```
Authorization: Bearer <access_token>
```

**Refresh token** (30 hari) hanya digunakan pada `POST /auth/refresh` untuk memperoleh access token baru tanpa login ulang.

**Token revocation.** JWT bersifat stateless — token tetap valid hingga kedaluwarsa meskipun user sudah logout. Untuk mengatasinya, `POST /auth/logout` menyimpan `jti` (JWT ID) token ke tabel `token_blocklist`. Setiap request yang terautentikasi memeriksa blocklist sebelum diproses, sehingga token yang sudah di-logout langsung ditolak.

**Role.** Role user disematkan sebagai custom claim di dalam token, sehingga pemeriksaan otorisasi tidak memerlukan query database pada setiap request. Konsekuensinya, perubahan role baru berlaku setelah token lama kedaluwarsa atau user login ulang.

---

## Testing

Test suite mencakup autentikasi, categories, products, dan orders, dengan kasus happy path maupun error case untuk setiap endpoint.

```bash
pytest -v
```

Test berjalan terhadap database terpisah (`TEST_DATABASE_URL`). Setiap test dimulai dari database kosong — tabel dibuat sebelum test dan dihapus setelahnya — sehingga test tidak saling mempengaruhi dan dapat dijalankan dalam urutan apa pun.

PostgreSQL digunakan untuk testing, bukan SQLite, agar perilaku yang diuji sama persis dengan production — khususnya row-level locking, foreign key constraint, pencarian case-insensitive, dan tipe numerik presisi tetap.

Menjalankan file tertentu:

```bash
pytest tests/test_orders.py -v
```

---

## Load Testing

```bash
flask run                    # terminal 1
locust                       # terminal 2
```

Buka `http://localhost:8089`, isi host dengan `http://127.0.0.1:5000`.

Skenario mensimulasikan perjalanan user: registrasi, melihat daftar produk, membuka detail produk, membuat order, lalu melihat order yang baru dibuat.

Hasil pengujian pada 200 concurrent user: 386 RPS, 0% failure, median response time 2–5 ms, 95th percentile di bawah 20 ms.

Pada pengujian dengan stock terbatas, sistem mengembalikan 409 Conflict untuk order yang melebihi ketersediaan tanpa satu pun stock menjadi negatif — memvalidasi bahwa row-level locking bekerja di bawah beban nyata.

---

## Catatan Desain

Beberapa keputusan berbeda dari spesifikasi awal, diambil secara sadar:

**Order dibatalkan, bukan dihapus.** Order adalah catatan transaksi yang diperlukan untuk riwayat dan audit. `POST /orders/<id>/cancel` mengubah status menjadi `cancelled` dan mengembalikan stock, alih-alih menghapus baris beserta seluruh order items-nya. Hanya order berstatus `pending` yang dapat dibatalkan — order yang sudah dibayar atau dikirim memerlukan proses refund atau retur, bukan sekadar perubahan kolom.

**Perubahan order dibatasi pada status.** Mengubah isi order berarti menghitung ulang selisih stock per item dan berisiko menghasilkan state yang tidak konsisten. `PUT /orders/<id>/status` hanya mengubah status; untuk mengubah isi, order dibatalkan lalu dibuat ulang.

**Registrasi berada di bawah `/auth`.** `POST /auth/register` dikelompokkan bersama endpoint autentikasi lain agar konsisten, alih-alih berdiri sendiri sebagai `POST /users`.

**Autentikasi menggunakan JWT.** Spesifikasi menyebut JWT sebagai opsional dan mengizinkan pengiriman `user_id` melalui request body. Pendekatan tersebut tidak diadopsi karena membuat siapa pun dapat mengaku sebagai user lain. JWT dipilih agar identitas pengguna berasal dari token yang tertandatangani, bukan dari input yang dapat dimanipulasi.

**Error handling terpusat.** Alih-alih blok `try/except` yang berulang di setiap route, penanganan error database dan exception tak terduga dipusatkan di global error handler. Setiap kegagalan menghasilkan rollback session, log detail di sisi server, dan response JSON yang aman di sisi client.

---

## Screenshots

Bukti pengujian dan struktur database tersedia di folder `img/`:

- Request Postman untuk setiap HTTP method (GET, POST, PUT, DELETE)
- Struktur tabel dan relasi di pgAdmin
- Diagram ERD
- Dashboard Locust pada 200 concurrent user

---

## Author

I Gede Ananda Bela Persada — RevoU Software Engineering
