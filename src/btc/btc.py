#!usr/bin/env python3
# -*- coding: utf-8 -*-
"""Module for interfacing with Büchi Temperature Controllers.

Written for Firmware V7.

RS232 Port Factory Settings
-------------------------------
BAUDRATE        4800 bauds
PARITY          even parity
HANDSHAKE       Protocol RTS/CTS (hardware handshake)
DATABITS        7
STOPBITS        1

Transfer Sequences
------------------
Transfer sequences are the queries sent to the temperature controller.
These byte sequences consist of a command and an optional parameter.
Each transfer sequence is terminated with \r.

The controller sends responses to 'in-commands' (without parameters)
that are terminated with '\r\n'. It does not respond to 'out-commands'.

Example queries:
Get working temperature 'T2'              b'in_sp_01\r'
Response:                                 b'24.04\r\n'

Set working temperature 'T1' to 12.4      b'out_sp_00 12.4\r'
Response                                  None

Author:         Nicolas Vetsch (veni@empa.ch / vetschnicolas@gmail.com)
Organisation:   EMPA Dübendorf, Materials for Energy Conversion (501)
Date:           2021-11-23

"""
import argparse
import csv
import logging
import time
import warnings
from datetime import datetime
from typing import Any, Union

import serial


class StatusError(Exception):
    """Raised when a 'status' query returns an error message."""


class BuchiTemperatureController(serial.Serial):
    """Class representing a Büchi Temperature Controller.

    This class inherits from the Serial class and extends it with all
    the property attributes of the Büchi Temperature Controller. Each
    property calls a querying function to get and set the corresponding
    values.

    Attributes
    ----------
    version ('version')
        Number of software version (V X.xx).
    status ('status')
        Status message, error message.
    temp_tj ('pv_00')
        Actual bath temperature.
    heating_power ('pv_01')
        Heating power being used (%).
    temp_tr ('pv_02')
        Temperature value registered by the Pt100 sensor „T-R“.
    temp_ts ('pv_03')
        Temperature value registered by the safety sensor „T-S“.
    temp_t1 ('sp_00')
        Working temperature "T1".
    temp_t2 ('sp_01')
        Working temperature "T2".
    high_temp_warning_limit ('sp_03')
        High temperature warning limit.
    low_temp_warning_limit ('sp_04')
        Low temperature warning limit.
    setpoint_temp ('sp_05')
        Setpoint temperature of the external programmer. (socket
        -REG+E-PROG)
    max_cooling_power ('hil_00')
        Max. cooling power (%).
    max_heating_power ('hil_01')
        Max. heating power (%).
    working_temp ('mode_01')
        Selected working temperature: 0 == "T1", 1 == "T2".
    id_type ('mode_02')
        Identification type: 0 == no identification,
        1 == single identification, 2 == continual identification.
    prog_input_type ('mode_03')
        Type of the programmer input: 0 == Voltage 0 V to 10 V,
        1 == Current 0 mA to 20 mA
    temp_control ('mode_04')
        Temperature control: 0 == Temperature control with Pt100 sensor
        „T-J“, 1 == Temperature control with Pt100 sensor „T-R“.
    start_stop ('mode_05')
        Circulator in Stop/Start condition:
        0 == Stop,
        1 == Start
    ext_bath_time_const ('par_01')
        Time constant of the external bath.
    int_slope ('par_02')
        Internal slope.
    int_bath_time_const ('par_03')
        Time constant of the internal bath.
    band_limiting ('par_04')
        Band limiting (max. difference between the temperatures in the
        internal bath and external system).
    max_ratio ('par_05')
        Ratio for max. cooling power versus max. heating power.
    xp_int ('par_06')
        Xp control parameter of the internal controller.
    tn_int ('par_07')
        Tn control parameter of the internal controller.
    tv_int ('par_08')
        Tv control parameter of the internal controller.
    xp_casc ('par_09')
        Xp control parameter of the cascade controller.
    proportional_portion_casc ('par_10')
        Proportional portion of the cascade controller.
    tn_casc ('par_11')
        Tn control parameter of the cascade controller.
    tv_casc ('par_12')
        Tv control parameter of the cascade controller.
    xpc_casc ('par_13')
        XpC control parameter of the cascade controller
    tnc_casc ('par_14')
        TnC control parameter of the cascade controller
    tvc_casc ('par_15')
        TvC control parameter ofthe cascade controller
    max_temp ('par_17')
        Maximum temperature T-J with controlling to T-R
    min_temp ('par_18')
        Minimum temperature T-J with controlling to T-R

    Methods
    -------
    query
        Sends a query and returns the temperature controller's response.
    log_csv
        Writes temperature controller data to a .csv file.

    """

    def __init__(
        self,
        *args,
        baudrate=4800,
        parity=serial.PARITY_EVEN,
        rtscts=True,
        bytesize=serial.SEVENBITS,
        stopbits=serial.STOPBITS_ONE,
        timeout=5,
        **kwargs,
    ) -> None:
        """Initializes a controller via the pyserial package."""
        super().__init__(
            *args,
            baudrate=baudrate,
            parity=parity,
            rtscts=rtscts,
            bytesize=bytesize,
            stopbits=stopbits,
            timeout=timeout,
            **kwargs,
        )

    @property
    def version(self) -> str:
        """Gets the software version."""
        return self.query("version")

    @property
    def status(self) -> str:
        """Gets a status message or error message."""
        return self.query("status")

    @property
    def temp_tj(self) -> str:
        """Gets the actual bath temperature."""
        return self.query("in_pv_00")

    @property
    def heating_power(self) -> str:
        """Gets the heating power being used (%)."""
        return self.query("in_pv_01")

    @property
    def temp_tr(self) -> str:
        """Gets the temperature value from the Pt100 sensor 'T-R'."""
        return self.query("in_pv_02")

    @property
    def temp_ts(self) -> str:
        """Gets the temperature value from the safety sensor 'T-S'."""
        return self.query("in_pv_03")

    @property
    def temp_t1(self) -> str:
        """Gets the working temperature 'T1'."""
        return self.query("in_sp_00")

    @temp_t1.setter
    def temp_t1(self, param) -> None:
        """Sets the working temperature 'T1'."""
        return self.query("out_sp_00", param)

    @property
    def temp_t2(self) -> str:
        """Gets the working temperature 'T2'."""
        return self.query("in_sp_01")

    @temp_t2.setter
    def temp_t2(self, param) -> None:
        """Sets the working temperature 'T2'."""
        return self.query("out_sp_01", param)

    @property
    def high_temp_warning_limit(self) -> str:
        """Gets the high temperature warning limit."""
        return self.query("in_sp_03")

    @high_temp_warning_limit.setter
    def high_temp_warning_limit(self, param) -> None:
        """Sets the high temperature warning limit."""
        return self.query("out_sp_03", param)

    @property
    def low_temp_warning_limit(self) -> str:
        """Gets the low temperature warning limit."""
        return self.query("in_sp_04")

    @low_temp_warning_limit.setter
    def low_temp_warning_limit(self, param) -> None:
        """Sets the low temperature warning limit."""
        return self.query("out_sp_04", param)

    @property
    def setpoint_temp(self) -> str:
        """Gets the setpoint temperature of the external programmer."""
        return self.query("in_sp_05")

    @property
    def max_cooling_power(self) -> str:
        """Gets the max. cooling power (%)."""
        return self.query("in_hil_00")

    @max_cooling_power.setter
    def max_cooling_power(self, param) -> None:
        """Sets the max. cooling power (%)."""
        return self.query("out_hil_00", param)

    @property
    def max_heating_power(self) -> str:
        """Gets the max. heating power (%)."""
        return self.query("in_hil_01")

    @max_heating_power.setter
    def max_heating_power(self, param) -> None:
        """Sets the max. heating power (%)."""
        return self.query("out_hil_01", param)

    @property
    def working_temp(self) -> str:
        """Gets the working temperature."""
        return self.query("in_mode_01")

    @working_temp.setter
    def working_temp(self, param) -> None:
        """Sets the working temperature."""
        return self.query("out_mode_01", param)

    @property
    def id_type(self) -> str:
        """Gets the identification type."""
        return self.query("in_mode_02")

    @id_type.setter
    def id_type(self, param) -> None:
        """Sets the identification type."""
        return self.query("out_mode_02", param)

    @property
    def prog_input_type(self) -> str:
        """Gets the programmer input type."""
        return self.query("in_mode_03")

    @property
    def temp_control(self) -> str:
        """Gets the temperature control sensor."""
        return self.query("in_mode_04")

    @temp_control.setter
    def temp_control(self, param) -> None:
        """Sets the temperature control sensor"""
        return self.query("out_mode_04", param)

    @property
    def start_stop(self) -> str:
        """Gets the temperature controller state."""
        return self.query("in_mode_05")

    @start_stop.setter
    def start_stop(self, param) -> None:
        """Sets the temperature controller state."""
        return self.query("out_mode_05", param)

    @property
    def ext_bath_time_const(self) -> str:
        """Gets tge time constant of the external bath."""
        return self.query("in_par_01")

    @property
    def int_slope(self) -> str:
        """Gets the internal slope."""
        return self.query("in_par_02")

    @property
    def int_bath_time_const(self) -> str:
        """Gets the time constant of the internal bath."""
        return self.query("in_par_03")

    @property
    def band_limiting(self) -> str:
        """Gets the max. difference between the temperatures in the
        internal bath and the external system."""
        return self.query("in_par_04")

    @band_limiting.setter
    def band_limiting(self, param) -> None:
        """Sets the max. difference between the temperatures in the
        internal bath and the external system."""
        return self.query("out_par_04", param)

    @property
    def max_ratio(self) -> str:
        """Gets the ratio of max. cooling power vs. max. heating power."""
        return self.query("in_par_05")

    @max_ratio.setter
    def max_ratio(self, param) -> None:
        """Sets the ratio of max. cooling power vs. max. heating power."""
        return self.query("out_par_05", param)

    @property
    def xp_int(self) -> str:
        """Gets the Xp control parameter of the internal controller."""
        return self.query("in_par_06")

    @xp_int.setter
    def xp_int(self, param) -> None:
        """Sets the Xp control parameter of the internal controller."""
        return self.query("out_par_06", param)

    @property
    def tn_int(self) -> str:
        """Gets the Tn control parameter of the internal controller."""
        return self.query("in_par_07")

    @tn_int.setter
    def tn_int(self, param) -> None:
        """Sets the Tn control parameter of the internal controller."""
        return self.query("out_par_07", param)

    @property
    def tv_int(self) -> str:
        """Gets the Tv control parameter of the internal controller."""
        return self.query("in_par_08")

    @tv_int.setter
    def tv_int(self, param) -> None:
        """Sets the Tv control parameter of the internal controller."""
        return self.query("out_par_08", param)

    @property
    def xp_casc(self) -> str:
        """Gets the Xp control parameter of the cascade controller."""
        return self.query("in_par_09")

    @xp_casc.setter
    def xp_casc(self, param) -> None:
        """Sets the Xp control parameter of the cascade controller."""
        return self.query("out_par_09", param)

    @property
    def proportional_portion_casc(self) -> str:
        """Gets the proportional portion of the cascade controller."""
        return self.query("in_par_10")

    @proportional_portion_casc.setter
    def proportional_portion_casc(self, param) -> None:
        """Sets the proportional portion of the cascade controller."""
        return self.query("out_par_10", param)

    @property
    def tn_casc(self) -> str:
        """Gets the Tn control parameter of the cascade controller."""
        return self.query("in_par_11")

    @tn_casc.setter
    def tn_casc(self, param) -> None:
        """Sets the Tn control parameter of the cascade controller."""
        return self.query("out_par_11", param)

    @property
    def tv_casc(self) -> str:
        """Gets the Tv control parameter of the cascade controller."""
        return self.query("in_par_12")

    @tv_casc.setter
    def tv_casc(self, param) -> None:
        """Sets the Tv control parameter of the cascade controller."""
        return self.query("out_par_12", param)

    @property
    def xpc_casc(self) -> str:
        """Gets the XpC control parameter of the cascade controller."""
        return self.query("in_par_13")

    @xpc_casc.setter
    def xpc_casc(self, param) -> None:
        """Sets the XpC control parameter of the cascade controller."""
        return self.query("out_par_13", param)

    @property
    def tnc_casc(self) -> str:
        """Gets the TnC control parameter of the cascade controller."""
        return self.query("in_par_14")

    @tnc_casc.setter
    def tnc_casc(self, param) -> None:
        """Sets the TnC control parameter of the cascade controller."""
        return self.query("out_par_14", param)

    @property
    def tvc_casc(self) -> str:
        """Gets the TvC control parameter of the cascade controller."""
        return self.query("in_par_15")

    @tvc_casc.setter
    def tvc_casc(self, param) -> None:
        """Sets the TvC control parameter of the cascade controller."""
        return self.query("out_par_15", param)

    @property
    def max_temp(self) -> str:
        """Gets the max. temperature 'T-J' with controlling to 'T-R'."""
        return self.query("in_par_17")

    @max_temp.setter
    def max_temp(self, param) -> None:
        """Sets the max. temperature 'T-J' with controlling to 'T-R'."""
        return self.query("out_par_17", param)

    @property
    def min_temp(self) -> str:
        """Gets the min. temperature 'T-J' with controlling to 'T-R'."""
        return self.query("in_par_18")

    @min_temp.setter
    def min_temp(self, param) -> None:
        """Sets the min. temperature 'T-J' with controlling to 'T-R'."""
        return self.query("out_par_18", param)

    def _check_status(self) -> None:
        """Checks for errors in the controller's status.

        The connection remains open even if an error is returned.

        Raises
        ------
        StatusError when the 'status' query returns an error code.

        """

    def query(self, command: str, param: Any = None) -> Union[str, None]:
        """Sends a query and returns the controller's response.

        The function puts together a transfer sequence from a given
        command (str) and parameter (Any). The response string is
        decoded from bytes and stripped of CRLF.

        Parameters
        ----------
        command
            The command to be sent to the temperature controller.
        param
            A parameter to set if the given command is an 'out-command'

        Returns
        -------
        str
            The decoded response of the controller.

        Raises
        ------
        StatusError
            When the 'status' query returns an error code after
            transmitting the given command.

        """
        resp = None
        if param is None:
            logging.debug("Tx: %s", command.encode() + b"\r")
            self.write(command.encode() + b"\r")
            resp = self.read_until(b"\r\n").decode().strip()
            logging.debug("Rx: %s", resp)
        elif "sp" in command:
            logging.debug(
                "Tx: %s", command.encode() + b" " + f"{param:.1f}".encode() + b"\r"
            )
            self.write(command.encode() + b" " + f"{param:.1f}".encode() + b"\r")
        else:
            logging.debug(
                "Tx: %s", command.encode() + b" " + f"{param:d}".encode() + b"\r"
            )
            self.write(command.encode() + b" " + f"{param:d}".encode() + b"\r")
        # The controller does not respond if it receives commands
        # without a little pause in between.
        time.sleep(0.05)
        # Always check the status to make sure there are no errors.
        self.write(b"status\r")
        status = self.read_until(b"\r\n")
        if status.startswith(b"-"):
            raise StatusError(status.decode())
        return resp

    def log_csv(self, timestep: float = 10.0, filepath: str = None) -> None:
        """Writes temperature controller data to a .csv file.

        The .csv will have columns ('Timestamp', 'Power', 'T-J', 'T-R',
        and 'T-S').

        Parameters
        ----------
        timestep
            The time interval between measurements in seconds. It takes
            a little less than a second to obtain and write all the
            values to a file so make sure to choose a timestep larger
            than 1.0 s.
        filepath
            Path to the .csv file to append to. Creates a new
            timestamped log file if None.

        """
        if timestep < 1.0:
            warnings.warn(
                f"Given timestep '{timestep}' may be too small to be "
                f"reflected in log. Consider using a larger timestep."
            )
        if filepath is None:
            now = datetime.now()
            filepath = now.strftime("%Y%m%dT%H%M%S") + "_btc_log" + ".csv"
        with open(filepath, "a+", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=",", lineterminator="\n")
            header = ["Timestamp", "Power [%]", "T-J [°C]", "T-R [°C]", "T-S [°C]"]
            writer.writerow(header)
            logging.info("%s", ", ".join(header))
            try:
                while True:
                    t0 = time.time()
                    row = [
                        datetime.now().isoformat(),
                        self.heating_power,
                        self.temp_tj,
                        self.temp_tr,
                        self.temp_ts,
                    ]
                    writer.writerow(row)
                    logging.info("%s", ", ".join(row))
                    t1 = time.time()
                    time.sleep(max(timestep - (t1 - t0), 0))
            except KeyboardInterrupt as interrupt:
                # Allow some time to clean up the buffers.
                time.sleep(0.05)
                self.reset_output_buffer()
                self.reset_input_buffer()
                raise interrupt


def logger():
    """Establishes a connection to a controller and starts to log.

    Entry point for `btc_logger` console script.

    This logger can be stopped via keyboard interrupt.

    """
    parser = argparse.ArgumentParser(
        description="Log temperature data from a Büchi temperature controller."
    )
    parser.add_argument(
        "port", help="The serial port connecting to the temperature controller.",
    )
    parser.add_argument(
        "-t",
        "--timestep",
        default=10.0,
        help="The time interval at which to log the controller data.",
        type=float,
    )
    parser.add_argument(
        "-f", "--filepath", default=None, help="Path to a file to append the log to."
    )
    args = parser.parse_args()
    # Connect and start to log.
    logging.basicConfig(level=logging.INFO)
    logging.info("Attempting to connect to btc on port %s.", args.port)
    btc = BuchiTemperatureController(args.port)
    if btc.is_open:
        logging.info("Connection established.")
    logging.info("Starting to log controller data every %s s.", args.timestep)
    btc.log_csv(timestep=args.timestep, filepath=args.filepath)
