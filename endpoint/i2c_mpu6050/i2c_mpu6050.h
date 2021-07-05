/**************************************************************************
 * I2C_MPU6050 library
 * Lucas Gabriel Cosmo Morais
 * 11/2020
 **************************************************************************/
#ifndef I2C_MPU6050_H
#define I2C_MPU6050_H

#include <libopencm3/stm32/i2c.h>

#define MPU_ADDR		0x68
#define PWR_MGMT_1		0x6B
#define PWR_MGMT_2		0x6C
#define INT_PIN_CFG		0x37
#define INT_ENABLE		0x38
#define INT_STATUS		0x3A
#define SMPRT_DIV		0x19
#define ACCEL_CONFIG	0x1C
#define ACCEL_XOUT_H	0x3B
#define ACCEL_YOUT_H	0x3D
#define ACCEL_ZOUT_H	0x3F

void i2c_write(uint32_t i2c, uint8_t dev_addr, uint8_t reg_addr, uint8_t data);
void i2c_request_data(uint32_t i2c, uint8_t dev_addr, uint8_t reg_addr, uint8_t n, uint8_t* buf);
void i2c_wakeup_mpu6050(uint32_t i2c);
void i2c_sleep_mpu6050(uint32_t i2c);
void i2c_setup_mpu6050(uint32_t i2c, uint8_t (*f)(void));

#endif // I2C_MPU6050_H
