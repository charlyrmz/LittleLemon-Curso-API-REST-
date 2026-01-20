# LittleLemon-Curso-API-REST-
API REST construida con Django + Django REST Framework, diseñada como backend para una app de restaurante. Implementa autenticación (Djoser / Token / opcional JWT), roles por grupos (Manager, Delivery crew, Customer), carrito, pedidos, categorías y menú con paginación, filtros y ordenamiento.

///////// Características principales /////////

- Registro y login con Djoser (/api/auth/users/, /api/auth/token/login/ o JWT según configuración).
- Roles y permisos mediante grupos: Manager y Delivery crew.
- CRUD de menu items: managers pueden crear/editar/eliminar; clientes y delivery crew pueden leer.
- Listado de categorías público.
- Carrito por usuario: añadir, listar y vaciar.
- Pedidos: crear pedido desde el carrito; managers pueden ver/editar/eliminar; delivery crew ve y actualiza pedidos asignados.
- Paginación, filtros y ordenamiento en /api/menu-items y /api/orders.
- Sanitización de campos de texto con bleach.
- Throttling básico configurado (anon y user).
- Manejo correcto de códigos HTTP y transacciones al crear pedidos.

///////// Estructura del proyecto /////////

LittleLemon/
  LittleLemon/          # settings, urls, wsgi, asgi
  LittleLemonAPI/       # app principal
    models.py
    serializers.py
    views.py
    urls.py
    permissions.py
    admin.py
    migrations/
db.sqlite3
manage.py
Pipfile / requirements.txt
README.txt

///////// Requisitos /////////

- Python 3.8+
- pipenv 
- Dependencias principales: Django, djangorestframework, djoser, django-filter, djangorestframework-simplejwt (opcional), bleach.

 ///////// Instalación rápida (con pipenv) /////////
Instalar dependencias y activar entorno:
- pipenv install
- pipenv shell

Instalar paquetes adicionales si faltan:
- pipenv install django djangorestframework djoser django-filter djangorestframework-simplejwt bleach

///////// Configuración y ejecución /////////

- Activar entorno:
pipenv shell

- Crear y aplicar migraciones:
python manage.py  makemigrations
python manage.py  migrate

- Crear superuser (interactivo):
python manage.py  createsuperuser

- Crear grupos (si no existen):
python manage.py  shell -c "from django.contrib.auth.models  import Group; Group.objects.get_or_create(name='Manager'); Group.objects.get_or_create(name='Delivery crew')"

- Ejecutar servidor:
python manage.py  runserver

///////// Endpoints principales /////////

Autenticación / usuarios (Djoser)

- POST /api/auth/users/         — crear usuario
- POST /api/auth/token/login/   — obtener token (si se usa token auth)
- GET  /api/auth/users/me/      — datos del usuario autenticado

Menu & categorías

- GET  /api/menu-items/         — listar (paginado, filtros, ordering, search)
- POST /api/menu-items/         — crear (Manager)
- GET  /api/menu-items/{id}/    — detalle
- PUT/PATCH/DELETE /api/menu-items/{id}/ — modificar/eliminar (Manager)
- GET  /api/categories/         — listar categorías

Grupos (Manager only)

- GET  /api/groups/manager/users                 — listar managers
- POST /api/groups/manager/users                 — asignar usuario a Manager (payload: {"username":"..."})
- DELETE /api/groups/manager/users/{userId}      — remover de Manager
- Análogos para delivery-crew en /api/groups/delivery-crew/users

Carrito (Customer)

- GET  /api/cart/menu-items       — ver carrito del usuario autenticado
- POST /api/cart/menu-items       — añadir item (payload: {"menu_item": id, "quantity": n})
- DELETE /api/cart/menu-items     — vaciar carrito

Pedidos

- GET  /api/orders                — customers: sus pedidos; manager: todos; delivery: asignados
- POST /api/orders                — crear pedido desde carrito (borra carrito)
- GET  /api/orders/{id}           — detalle (con permisos)
- PATCH /api/orders/{id}          — delivery: actualizar status; manager: asignar delivery_crew y status
- DELETE /api/orders/{id}         — manager elimina pedido

///////// Paginación, filtros y ordenamiento /////////

Paginación por defecto: PAGE_SIZE configurado en settings (ej. 5).

Parámetros útiles:
- ?page=2
- ?page_size=10
- ?ordering=price  (o -price para descendente)
- ?search=texto
- filtros por campos configurados: ?category=1, ?featured=True
