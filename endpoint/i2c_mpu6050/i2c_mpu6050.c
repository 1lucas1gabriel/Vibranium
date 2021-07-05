/**************************************************************************
 * I2C_MPU6050 library
 * Lucas Gabriel Cosmo Morais
 * 11/2020
 **************************************************************************/

#include "i2c_mpu6050.h"


void i2c_write(uint32_t i2c, uint8_t dev_addr, uint8_t reg_addr, uint8_t data){

	while ((I2C_SR2(i2c) & I2C_SR2_BUSY));
	i2c_send_start(i2c);

	// Wait for the end of the start condition, master mode selected, and BUSY bit set
	while (!((I2C_SR1(i2c) & I2C_SR1_SB)
		& (I2C_SR2(i2c) & (I2C_SR2_MSL | I2C_SR2_BUSY))));
  
	i2c_send_7bit_address(i2c, dev_addr, I2C_WRITE);

	// Waiting for address is transferred
	while (!(I2C_SR1(i2c) & I2C_SR1_ADDR));
  
	// Clearing ADDR condition sequence
	(void)I2C_SR2(i2c);
	
	// write to register address  
	i2c_send_data(i2c, reg_addr);
	while (!(I2C_SR1(i2c) & (I2C_SR1_BTF)));

	// write data to register  
	i2c_send_data(i2c, data);
	while (!(I2C_SR1(i2c) & (I2C_SR1_BTF)));

	i2c_send_stop(i2c);
}


void i2c_request_data(uint32_t i2c, uint8_t dev_addr, 
						uint8_t reg_addr, uint8_t n, uint8_t* buf){
	
	uint8_t i = 0;
	//---------------------------------------------------------------------------
	// First, We send a write to device and register we want to read
	//---------------------------------------------------------------------------	
	while ((I2C_SR2(i2c) & I2C_SR2_BUSY));
	i2c_send_start(i2c);

	// Wait for the end of the start condition, master mode selected, and BUSY bit set
	while (!((I2C_SR1(i2c) & I2C_SR1_SB)
		& (I2C_SR2(i2c) & (I2C_SR2_MSL | I2C_SR2_BUSY))));
  
	i2c_send_7bit_address(i2c, dev_addr, I2C_WRITE);

	// Waiting for address is transferred
	while (!(I2C_SR1(i2c) & I2C_SR1_ADDR));
  
	// Clearing ADDR condition sequence
	(void)I2C_SR2(i2c);
	
	// write to register address  
	i2c_send_data(i2c, reg_addr);
	while (!(I2C_SR1(i2c) & (I2C_SR1_BTF)));

	//---------------------------------------------------------------------------
	// Now, we send a read request to device (at the register we request before)
	//---------------------------------------------------------------------------
	
	i2c_send_start(i2c);
	i2c_enable_ack(i2c);
  
	/* Wait for the end of the start condition, master mode selected, and BUSY bit set */
	while (!((I2C_SR1(i2c) & I2C_SR1_SB)
		& (I2C_SR2(i2c) & (I2C_SR2_MSL | I2C_SR2_BUSY))));
  
	i2c_send_7bit_address(i2c, dev_addr, I2C_READ);
 	
	/* Waiting for address is transferred. */
	while (!(I2C_SR1(i2c) & I2C_SR1_ADDR));

	/* Clearing ADDR condition sequence. */
	(void)I2C_SR2(i2c);

	// Burst read method  
	while(i < n){
		while (!(I2C_SR1(i2c) & I2C_SR1_RxNE));		
		buf[i] = i2c_get_data(i2c);
		
		if(i == n - 1)
			i2c_disable_ack(i2c);			
		++i;
	}
	i2c_send_stop(i2c);
}


void i2c_wakeup_mpu6050(uint32_t i2c){

	i2c_write(i2c, MPU_ADDR, PWR_MGMT_1, 0x0);
}


void i2c_sleep_mpu6050(uint32_t i2c){

	i2c_write(i2c, MPU_ADDR, PWR_MGMT_1, 0x40);
}


void i2c_setup_mpu6050(uint32_t i2c, uint8_t (*f)(void)){
	
	uint8_t config = f();

	// Setup sensitivity
	switch(config & 0xF){
		case 1:
			i2c_write(i2c, MPU_ADDR, ACCEL_CONFIG, 0x00);
			break;
		case 2:
			i2c_write(i2c, MPU_ADDR, ACCEL_CONFIG, 0x08);
			break;
		case 4:
			i2c_write(i2c, MPU_ADDR, ACCEL_CONFIG, 0x10);
			break;
		case 8:
			i2c_write(i2c, MPU_ADDR, ACCEL_CONFIG, 0x18);
			break;
	}
}




















