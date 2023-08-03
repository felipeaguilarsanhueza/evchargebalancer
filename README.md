## EV Charge Balancer

EV Charge Balancer es una aplicación web que permite gestionar la carga de vehículos eléctricos de forma eficiente y equilibrada. La aplicación utiliza programación lineal para distribuir la corriente entre los cargadores controlados y los cargadores VIP, optimizando el uso de la energía y evitando sobrecargas en la red eléctrica.

### Características

- Permite configurar los límites de corriente para cada hora del día.
- Permite definir la cantidad de cargadores VIP y cargadores controlados.
- Calcula la distribución óptima de corriente entre los cargadores.
- Genera un gráfico de corriente acumulada para cada cargador.
- Muestra los valores de corriente para cada hora y cada cargador en tablas separadas.
- Permite reiniciar la configuración a los valores predeterminados.

### Uso

1. Clona el repositorio en tu máquina local:

```shell
git clone https://github.com/tu-usuario/ev-charge-balancer.git
```

2. Instala las dependencias necesarias:

```shell
pip install -r requirements.txt
```

3. Ejecuta la aplicación:

```shell
python evchargebalancer.py
```

4. Accede a la aplicación en tu navegador web a través de la siguiente URL:

```
http://localhost:5000/
```

### Demo

Puedes probar una demostración de la aplicación en el siguiente enlace de Heroku:

[Demo de EV Charge Balancer]([https://evchargebalancer-ca54350e9a09.herokuapp.com/](https://evchargebalancer-0uh1-dev.fl0.io/))

### Contribuciones

Si deseas contribuir a EV Charge Balancer, sigue estos pasos:

1. Haz un fork del repositorio.
2. Crea una rama para tu contribución:
```shell
git checkout -b mi-contribucion
```
3. Realiza tus cambios y realiza commits con mensajes descriptivos.
4. Envía un pull request indicando los cambios realizados.

### Licencia

Este proyecto se encuentra bajo la Licencia [MIT](https://opensource.org/licenses/MIT).
