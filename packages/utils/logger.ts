export const logger = {
  log: (serviceId: string, msg: string, context?: any) => {
    console.log(JSON.stringify({
      level: "INFO",
      timestamp: new Date().toISOString(),
      serviceId,
      msg,
      context
    }));
  },
  error: (serviceId: string, msg: string, context?: any) => {
    console.error(JSON.stringify({
      level: "ERROR",
      timestamp: new Date().toISOString(),
      serviceId,
      msg,
      context
    }));
  }
};
