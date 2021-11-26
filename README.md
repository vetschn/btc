# Büchi Temperature Controller

Python package for interfacing with Büchi Temperature Controllers *btc01*/*btc02* via the RS232 serial port making use of [pySerial](https://pyserial.readthedocs.io/en/latest/pyserial.html).

*Written for btc Firmware V7.*

## Example Usage

The `BuchiTemperatureController` class extends the [`serial.Serial`](https://pyserial.readthedocs.io/en/latest/pyserial_api.html#serial.Serial) class. To instantiate, simply pass the port name, e.g. `'COM3'`, to the `BuchiTemperatureController` initializer. Port factory settings are assumed (see [About the Device](#about-the-device)).

All the available attributes of the Büchi Temperature Controller are implemented as class properties. Each property calls a querying function `query` to get and set the corresponding values via the serial port.

There is also a logging function `log_csv` that continually writes .csv logs for heating power and temperatures 'T-J', 'T-R', and 'T-S' at a given time interval.

### Example 1
Get the software version number
```python
>>> from btc import BuchiTemperatureController
>>> btc = BuchiTemperatureController('COM3')
>>> btc.version

```
### Example 2
Set the working temperature 'T1' to 12.4 °C
```python
>>> from btc import BuchiTemperatureController
>>> btc = BuchiTemperatureController('COM3')
>>> btc.query("out_sp_00", 12.4)
>>>
```
### Example 3
Log the heating power percentage and the temperatures 'T-J', 'T-R', and 'T-S' to a .csv file every 10s.
```python
>>> from btc import BuchiTemperatureController
>>> btc = BuchiTemperatureController('COM3')
>>> btc.log_csv(timestep=10)

```

After installing the package, you can also use the `btc_logger` console command.
```
> cd btc
> pip install .
...
> btc_logger -h
usage: btc_logger [-h] [-t TIMESTEP] [-f FILEPATH] port

Log temperature data from a Büchi temperature controller.

positional arguments:
  port                  The serial port connecting to the temperature controller.

options:
  -h, --help            show this help message and exit
  -t TIMESTEP, --timestep TIMESTEP
                        The time interval at which to log the controller data.
  -f FILEPATH, --filepath FILEPATH
                        Path to a file to append the log to.
```

## About the Device

Some info on the serial port remote control of the *btc01*/*btc02* as explained in the operating manual.

### RS232 Port Factory Settings
|           |         |
|-----------|---------|
| BAUDRATE  | 4800 Bd |
| PARITY    | Even    |
| HANDSHAKE | RTS/CTS |
| DATABITS  | 7       |
| STOPBITS  | 1       |


### Transfer Sequences

Transfer sequences are the queries sent to the temperature controller. These byte sequences consist of a command and optionally a parameter.
Each transfer sequence is terminated with `\r`.

The controller sends responses to "in-commands" (query commands *without* parameters). These responses are terminated with `\r\n`.

So-called "out-commands" (query commands *with* parameters) do not prompt a response.

### Example Queries
1. Get working temperature 'T2'
    ```python
    Tx: b'in_sp_01\r'
    Rx: b'24.04\r\n'
    ```
2. Set working temperature 'T1' to 12.4 °C
    ```python
    Tx: b'out_sp_00 12.4\r'
    Rx:
    ```

### Commands

All of the commands (except for `'version'`, `'status'`, and `'REMOTE'`) can be prepended by either `in_` (get) or `out_` (set) to get or set the corresponding value. Setting is not possible for all of them. 

Make sure to consult the operating manual.

| Command     | Description |
|-------------|-------------|
| `'version'` | Number of software version (V X.xx). |
| `'status'`  | Status message, error message. |
| `'REMOTE'`  | Change the preset value. |
| `'pv_00'`   | Actual bath temperature. |
| `'pv_01'`   | Heating power being used (%). |
| `'pv_02'`   | Temperature value registered by the Pt100 sensor 'T-R. |
| `'pv_03'`   | Temperature value registered by the safety sensor 'T-S'. |
| `'sp_00'`   | Working temperature 'T1'. |
| `'sp_01'`   | Working temperature 'T2'. |
| `'sp_03'`   | High temperature warning limit. |
| `'sp_04'`   | Low temperature warning limit. |
| `'sp_05'`   | Setpoint temperature of the external programmer. |
| `'hil_00'`  | Max. cooling power (%). |
| `'hil_01'`  | Max. heating power (%). |
| `'mode_01'` | Selected working temperature. <br> 0 == "T1", <br> 1 == "T2". |
| `'mode_02'` | Identification type. <br> 0 == no identification, <br> 1 == single identification, <br> 2 == continual identification. |
| `'mode_03'` | Type of the programmer input. <br> 0 == Voltage 0 V to 10 V, <br> 1 == Current 0 mA to 20 mA |
| `'mode_04'` | Temperature control. <br> 0 == Temperature control with Pt100 sensor 'T-J', <br> 1 == Temperature control with Pt100 sensor 'T-R'. |
| `'mode_05'` | Circulator in Stop/Start condition. <br> 0 == Stop, <br> 1 == Start |
| `'par_01'`  | Time constant of the external bath. |
| `'par_02'`  | Internal slope. |
| `'par_03'`  | Time constant of the internal bath. |
| `'par_04'`  | Band limiting (max. difference between the temperatures in the internal bath and external system). |
| `'par_05'`  | Ratio for max. cooling power versus max. heating power. |
| `'par_06'`  | Xp control parameter of the internal controller. |
| `'par_07'`  | Tn control parameter of the internal controller. |
| `'par_08'`  | Tv control parameter of the internal controller. |
| `'par_09'`  | Xp control parameter of the cascade controller. |
| `'par_10'`  | Proportional portion of the cascade controller. |
| `'par_11'`  | Tn control parameter of the cascade controller. |
| `'par_12'`  | Tv control parameter of the cascade controller. |
| `'par_13'`  | XpC control parameter of the cascade controller. |
| `'par_14'`  | TnC control parameter of the cascade controller. |
| `'par_15'`  | TvC control parameter ofthe cascade controller.|
| `'par_17'`  | Maximum temperature 'T-J' with controlling to 'T-R'.|
| `'par_18'`  | Minimum temperature 'T-J' with controlling to 'T-R'.|
