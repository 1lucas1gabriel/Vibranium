/**************************************************************************
 * MAIN PROGRAM - ACCELEROMETER BLE SYSTEM
 * @1lucas1gabriel - NOV/20
 *
 * USART1
 * PA9(TX)  --> AT-09 BLE (RX)
 * PA10(RX) --> AT-09 BLE (TX)
 * PA15	    --> AT-09 BLE (VCC)
 *
 * I2C1
 * PB6(SCL) --> (SCL) MPU6050
 * PB7(SDA) --> (SDA) MPU6050
 *
 * DEVELOPMENT LOGS
 * 1 - GPIO setup
 * 2 - USART echo program
 * 3 - Development and configuration of I2C functions and perph's
 * 4 - RTC and alarm configuration
 * 5 - Standy configuration (SLEEPDEEP System register and functions)
 * 6 - Slow down clock from 72Mhz to 24Mhz (to decrease current consumption)
 * 7 - Change I2C2 to I2C1 (pinout reasons)
 * 8 - BLE connection library
 * 9 - User configuration/ config mode					
 * 10 - Acquision function with 1ms TIMER
 * 11 - BLE send with trigger 20 ms TIMER
 **************************************************************************/

#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/gpio.h>
#include <libopencm3/stm32/usart.h>
#include <libopencm3/stm32/i2c.h>
#include <libopencm3/stm32/rtc.h>
#include <libopencm3/stm32/pwr.h>
#include <libopencm3/stm32/timer.h>
#include <libopencm3/stm32/f1/bkp.h>
#include <libopencm3/cm3/scb.h>
#include <libopencm3/cm3/nvic.h>
#include "i2c_mpu6050.h"
#include "ble_usart.h"

#define CONFIG_DEVICE	0
#define RUNNING		1
#define READING_DATA	0
#define SENDING_DATA	1
#define i2c		I2C1
#define usart		USART1
#define NUM_SAMPLES	1024
#define BUFFER_SIZE	6 * NUM_SAMPLES

volatile bool timer_mode = READING_DATA;
volatile bool request_mpu6050 = false;
volatile bool ble_send_packet = false;

/**************************************************************************
 * PROTOTIPES
 **************************************************************************/
static void clock_setup(void);
static void gpio_setup(void); // DEBUG ONLY
static void usart_setup(void);
static void i2c_setup(void);
static void timer2_setup(uint8_t ticks);
static void timer2_disable(void);

static void powerOn_ble(void);
static void powerOff_ble(void);
static void ledOn(void);
static void ledOff(void);

static void rtc_setup(void);
static bool check_stdby(void);
static void set_alarm(uint8_t (*f)(void));
static void enter_stdby(void);

static void save_devconfig(void);
uint8_t get_devconfig(void);

static void serial_write(uint8_t *buf, uint16_t begin, uint8_t n);
static void serial_write_bin(uint8_t buf); // DEBUG ONLY

static uint8_t *data_aquisition(void);
static void ble_send_data(uint8_t *buffer);
static void delay(uint8_t value);


/**************************************************************************
 * MAIN PROGRAM
 **************************************************************************/
int main(void){
		
	bool Mode;
	Mode = check_stdby();

	clock_setup();
	gpio_setup();
	rtc_setup();

	if(Mode == RUNNING){
		// TO DO: disable gyroscope and temperature sensor

		//-----------------------------------------//
		// SETUP ACCELEROMETER AND AQUISITION DATA //
		//-----------------------------------------//
		i2c_setup();
		i2c_wakeup_mpu6050(i2c);
		i2c_setup_mpu6050(i2c, get_devconfig);

		timer_mode = READING_DATA;
		timer2_setup(10);
		ledOn();				// DEBUG ONLY
		uint8_t *p_buf = data_aquisition();
		ledOff();				// DEBUG ONLY
		timer2_disable();

		//---------------------------------//
		// BLE CONNECTION AND DATA SENDING //
		//---------------------------------//
		
		powerOn_ble();
		usart_setup();
		while(!ble_connected());
		ledOn();				// DEBUG ONLY

		// wait command for sending data
		while(!ble_recv_cmd('1'));
		ledOff();				// DEBUG ONLY

		timer_mode = SENDING_DATA;
		timer2_setup(200);
		ledOn();				// DEBUG ONLY
		ble_send_data(p_buf);
		timer2_disable();
	
		// Waiting disconnection
		while(!ble_recv_cmd('0'));
		delay(10);
		ledOff();				// DEBUG ONLY
		powerOff_ble();
	}

	if(Mode == CONFIG_DEVICE){
	
		powerOn_ble();
		usart_setup();

		// wait for connection with user
		while(!ble_connected());
		ledOn();				// DEBUG ONLY

		// wait for user config
		while(!ble_recv_config());
		ledOff();				// DEBUG ONLY

		save_devconfig();
		powerOff_ble();
	}
	set_alarm(get_devconfig);
	enter_stdby();	

	return 0;
}


/**************************************************************************
 * SETUP CLOCK SISTEM (SYSCLOCK)
 **************************************************************************/
static void clock_setup(void){

	rcc_clock_setup_in_hse_8mhz_out_24mhz();
}


/**************************************************************************
 * GPIO SETUP - LED (DEBUG ONLY)
 **************************************************************************/
static void gpio_setup(void){
	
	rcc_periph_clock_enable(RCC_GPIOA); // LED
	gpio_set_mode(
			GPIOA,
			GPIO_MODE_OUTPUT_2_MHZ,
			GPIO_CNF_OUTPUT_PUSHPULL,
			GPIO8);
	ledOff();
}


/**************************************************************************
 * UART SETUP
 **************************************************************************/
static void usart_setup(void){
	
	rcc_periph_clock_enable(RCC_GPIOA);	// USART1
	rcc_periph_clock_enable(RCC_USART1);	// USART1

	// enable the USART1 interrupt
	nvic_enable_irq(NVIC_USART1_IRQ);

	// setup USART1_TX
	gpio_set_mode(
			GPIOA,
			GPIO_MODE_OUTPUT_10_MHZ,
			GPIO_CNF_OUTPUT_ALTFN_PUSHPULL,
			GPIO_USART1_TX);

	// setup USART1_RX
	gpio_set_mode(
			GPIOA,
			GPIO_MODE_INPUT,
			GPIO_CNF_INPUT_FLOAT,
			GPIO_USART1_RX);

	// setup USART1 parameters
	usart_set_baudrate(	usart, 115200);
	usart_set_databits(	usart, 8);
	usart_set_stopbits(	usart, USART_STOPBITS_1);
	usart_set_mode(		usart, USART_MODE_TX_RX);
	usart_set_parity(	usart, USART_PARITY_NONE);
	usart_set_flow_control(	usart,	USART_FLOWCONTROL_NONE);

	// enable USART1 receive interrupt
	USART_CR1(usart) |= USART_CR1_RXNEIE;
	
	// Finally enable usart
	usart_enable(usart);
}


/**************************************************************************
 * ISR USART RX - READ RX AND SET A FLAG
 **************************************************************************/
void usart1_isr(void){

	// Check if we were called because of RXNE
	if(((USART_CR1(usart) & USART_CR1_RXNEIE) != 0) &&
	 ((USART_SR(usart) & USART_SR_RXNE) != 0)){
		
		// volatile variables from ble_usart.h
		usart_rx_data = usart_recv(usart);
		flag_read_usart = true;
	}
}


/**************************************************************************
 * I2C SETUP
 **************************************************************************/
static void i2c_setup(void){
	
	rcc_periph_clock_enable(RCC_I2C1);
	rcc_periph_clock_enable(RCC_GPIOB);	// I2C
	rcc_periph_clock_enable(RCC_AFIO);	// EXTI

	// Set alternate functions for the SCL and SDA pins of I2C1
	gpio_set_mode(GPIOB, GPIO_MODE_OUTPUT_10_MHZ,
		      GPIO_CNF_OUTPUT_ALTFN_OPENDRAIN,
		      GPIO_I2C1_SCL | GPIO_I2C1_SDA);

	i2c_reset(i2c);
	i2c_peripheral_disable(i2c);
	//----------------------------------//
	// Standard Mode: i2c_speed_sm_100k //
	// Fast Mode:     i2c_speed_fm_400k //
	//----------------------------------//
	i2c_set_speed(i2c, i2c_speed_fm_400k, 24); // 24MHZ
	i2c_peripheral_enable(i2c);
}


/**************************************************************************
 * PROGRAMABLE MILISSECOND TIMER
 **************************************************************************/
static void timer2_setup(uint8_t ticks){

	// Enable TIM2 clock and interrupt 
	rcc_periph_clock_enable(RCC_TIM2);
	nvic_enable_irq(NVIC_TIM2_IRQ);

	//--------------------------------------------------//
	// APB1 is running at 24MHZ --> APB1 prescaler = 1  //
	// timer2 freq = APB1 / 2400 = 10 kHz               //
	// (1/10kHz) x 10 ticks [0:9] = 1ms                 //
	// (1/10kHz) x 200 ticks [0:99] = 10ms              //
	//--------------------------------------------------//
	
	timer_set_prescaler(TIM2, 2400);
	timer_set_period(TIM2, ticks - 1); 

	timer_enable_irq(TIM2, TIM_DIER_UIE);
	timer_enable_counter(TIM2);
}


/**************************************************************************
 * DISABLE COUNTER AND INTERRUPT
 **************************************************************************/
static void timer2_disable(void){
	
	// disable to next the configuration
	timer_disable_counter(TIM2);
	timer_disable_irq(TIM2, TIM_DIER_UIE);
	rcc_periph_clock_disable(RCC_TIM2);
}


/**************************************************************************
 * ISR TIMER2 - TIMER USED TO READ ACCEL AND SEND BLE DATA
 **************************************************************************/
void tim2_isr(void){

	// Clear interrupt flag
	timer_clear_flag(TIM2, TIM_SR_UIF);
	
	//--------------------------------------------------------------//
	// TIMER MODE							//
	// (READIND_DATA): Timer is used for 1kHz aquisition		//
	// (SENDING_DATA): Timer is used to limit BLE output data rate	//
	//--------------------------------------------------------------//
	if(timer_mode == READING_DATA){	
		request_mpu6050 = true;
	}
	if(timer_mode == SENDING_DATA){
		ble_send_packet = true;
	}
}


/**************************************************************************
 * TURN ON BLE POWER
 **************************************************************************/
static void powerOn_ble(void){

	// GPIO A15 - POWER SOURCE BLE MODULE
	rcc_periph_clock_enable(RCC_GPIOA);
	gpio_set_mode(
			GPIOA,
			GPIO_MODE_OUTPUT_2_MHZ,
			GPIO_CNF_OUTPUT_PUSHPULL,
			GPIO12);

	// turn on BLE
	gpio_set(GPIOA, GPIO12);	
}


/**************************************************************************
 * TURN OFF BLE POWER
 **************************************************************************/
static void powerOff_ble(void){

	// turn off ble
	gpio_clear(GPIOA, GPIO12);
	rcc_periph_clock_disable(RCC_GPIOA);
}


/**************************************************************************
 * TURN ON LED
 **************************************************************************/
static void ledOn(void){

	gpio_set(GPIOA, GPIO8);
}


/**************************************************************************
 * TURN OFF LED
 **************************************************************************/
static void ledOff(void){

	gpio_clear(GPIOA, GPIO8);
}


/**************************************************************************
 * RTC SETUP (1 SECOND)
 **************************************************************************/
static void rtc_setup(void){	
	
	rtc_interrupt_disable(RTC_SEC);
	rtc_interrupt_disable(RTC_ALR);
	
	// External cristal freq: 32.768k/Prescaller => 1 sec 
	rtc_auto_awake(RCC_LSE, 0x7fff);
	rtc_set_counter_val(0x0);

	nvic_enable_irq(NVIC_RTC_IRQ);
	nvic_set_priority(NVIC_RTC_IRQ, 1);
	
	rtc_clear_flag(RTC_SEC);
	rtc_clear_flag(RTC_ALR);
}


/**************************************************************************
 * ISR RTC
 **************************************************************************/
void rtc_isr(void){

	if(rtc_check_flag(RTC_SEC))
		rtc_clear_flag(RTC_SEC);

	if (rtc_check_flag(RTC_ALR))
		rtc_clear_flag(RTC_ALR);
}


/**************************************************************************
 * CHECKS IF WE CAME FROM STANDBY MODE
 **************************************************************************/
static bool check_stdby(void){

	// If we came from stdby device is in running mode
	if(pwr_get_standby_flag())
		return true;
	else
		return false;
}


/**************************************************************************
 * SET AN ALARM N SECONDS INTO THE FUTURE
 **************************************************************************/
static void set_alarm(uint8_t (*f)(void)){
	
	uint8_t config = f();
	
	rtc_disable_alarm();

	// Setup user alarm_timer 
	switch(config & 0xF0){
		case 16:
			rtc_set_alarm_time(rtc_get_counter_val() + 5);
			break;
		case 32:
			rtc_set_alarm_time(rtc_get_counter_val() + 10);
			break;
		case 64:
			rtc_set_alarm_time(rtc_get_counter_val() + 20);
			break;
		case 128:
			rtc_set_alarm_time(rtc_get_counter_val() + 30);
			break;
	}
	rtc_enable_alarm();
	
	// Enable interruptions now
	rtc_interrupt_enable(RTC_SEC);
	rtc_interrupt_enable(RTC_ALR);
}


/**************************************************************************
 * ENTER STANDBY MODE
 **************************************************************************/
static void enter_stdby(void){
	
	rcc_periph_clock_enable(RCC_PWR);
	
	SCB_SCR |= (1 << 2);
	pwr_set_standby_mode();
	pwr_clear_wakeup_flag();	
	__asm("wfi");
}


/**************************************************************************
 * SET USER CONFIG TO BACKUP IN CONFIG_DEVICE MODE
 **************************************************************************/
static void save_devconfig(void){

	// Enable power and backup interface clocks
	rcc_periph_clock_enable(RCC_PWR);
	rcc_periph_clock_enable(RCC_BKP);

	// Allow backup domain registers to be changed
	pwr_disable_backup_domain_write_protect();

	//-----------------------------------------------------//
	// Save accel and rtc config at 16 bit BKP register    //
	// STM32F1 - Medium density: 10 DR x 16 bit = 20 bytes //
	// BKP_DR1: BACKUP_REGS_BASE + 0x04                    //
	//-----------------------------------------------------//
	
	// clear all bits
	BKP_DR1 = 0;	

	switch(devconfig.sensitivity){
		case '0':
				BKP_DR1 |= (1 << 0);
				break;
		case '1':
				BKP_DR1 |= (1 << 1);
				break;
		case '2':
				BKP_DR1 |= (1 << 2);
				break;
		case '3':
				BKP_DR1 |= (1 << 3);
				break;
	}
	switch(devconfig.alarm_timer){
		case 'A':
				BKP_DR1 |= (1 << 4);
				break;
		case 'B':
				BKP_DR1 |= (1 << 5);
				break;
		case 'C':
				BKP_DR1 |= (1 << 6);
				break;
		case 'D':
				BKP_DR1 |= (1 << 7);
				break;
	}
}


/**************************************************************************
 * GET USER CONFIG FROM BACKUP IN RUNNING MODE
 **************************************************************************/
uint8_t get_devconfig(void){

	uint8_t reg8 = 0;
	
	// Enable power and backup interface clocks
	rcc_periph_clock_enable(RCC_PWR);
	rcc_periph_clock_enable(RCC_BKP);

	// Allow backup domain registers to be changed
	pwr_disable_backup_domain_write_protect();

	// get 8 bits from BKP_DR1
	reg8 |= (BKP_DR1 & 0x00FF);

	return reg8;
}


/**************************************************************************
 * SEND N SERIAL DATA FROM A BUFFER (USART)
 **************************************************************************/
static void serial_write(uint8_t *buf, uint16_t begin, uint8_t n){
	
	for(uint8_t offset = 0; offset < n; ++offset){
		usart_send_blocking(usart, buf[begin + offset]);
	}
	usart_send_blocking(usart, '\r');
	usart_send_blocking(usart, '\n');
}


/**************************************************************************
 * SEND SERIAL DATA - BINARY MODE (USART1) - FOR DEBUG ONLY
 **************************************************************************/
static void serial_write_bin(uint8_t buf){

	// Send data as binary over USART
	for (int i = 7; i >= 0; i--) {
		if (buf & (1 << i))
			usart_send_blocking(usart, '1');
		else
			usart_send_blocking(usart, '0');
	}
	usart_send_blocking(usart, '\r');
	usart_send_blocking(usart, '\n');
}


/**************************************************************************
 * ACCELEROMETER DATA AQUISITION
 **************************************************************************/
static uint8_t *data_aquisition(){
	
	uint16_t 		sample = 0;
	uint16_t 		offset = 0;
	static uint8_t 	accel_buffer[BUFFER_SIZE];
	
	//--------------------------------------//
	// Aquisition: 3 axis (each of 2 bytes) //
	// number of samples: 1024              //
	// 6 bytes * 1024 = 6144 bytes          //
	//--------------------------------------//
	
	while(sample < NUM_SAMPLES){

		// resquest_mpu6050 flag at 1kHz
		if(request_mpu6050){
			i2c_request_data(i2c, MPU_ADDR, ACCEL_XOUT_H, 6, accel_buffer + offset);
			++sample;
			offset += 6;
			request_mpu6050 = false;
		}
	}
	return accel_buffer;
}


/**************************************************************************
 * BLE SEND DATA AQUISITION
 **************************************************************************/
static void ble_send_data(uint8_t *buffer){
	
	uint16_t sample = 0;
	uint16_t remaining_samples = 0;
	
	//--------------------------------------------------------------//
	// ble_send_packet flag at 200Hz (20 ms)			//
	//								//
	// payload size: 3 axis * 2 bytes/axis * 3 samples = 18 bytes	//
	// payload full: 18 bytes + '\r' + '\n' =  20 bytes		// 
	//								//
	// PACKET FORMAT: (Ax_H, Ax_L, Ay_H, Ay_L, Az_H, Az_L )		//
	//								//
	// DATA	FORMAT:		int16_t Ax = (Ax_H << 8) | Ax_L		//
	// Ax_H	uint8_t		int16_t Ay = (Ay_H << 8) | Ay_L		//
	// Ax_L	uint8_t		int16_t Az = (Az_H << 8) | Az_L		//
	//--------------------------------------------------------------//

	while(sample < NUM_SAMPLES){
		if(ble_send_packet){
			ble_send_packet = false;

			//-----------------------------------------------//
			// send remaining packets of accel buffer [1023] //
			//-----------------------------------------------//			
			remaining_samples = NUM_SAMPLES - sample;
			if(remaining_samples < 3){
				if(remaining_samples == 1){
					serial_write(buffer, 6*sample, 6);
					++sample;
				}
			
			}
			//---------------------------------------------------//
			// send 3 sample per packet of accel buffer [0:1022] //
			//---------------------------------------------------//
			else{
				serial_write(buffer, 6*sample, 18);
				sample += 3;
			}
		}
	}
}

/**************************************************************************
 * WASTE CPU RESOURCES - I'm sorry bluepill, I promise I'll use RTOS :(
 **************************************************************************/
static void delay(uint8_t value){

	for(uint32_t j=0; j<(value*1000000); ++j)
		__asm__("nop");
}
