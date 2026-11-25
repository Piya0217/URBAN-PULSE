
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
  timeout: 10000,
})

// Accident APIs
export const getYearlyAccidents = async () => {
  const response = await api.get('/api/accidents/yearly')
  return response.data
}

export const getAccidentZones = async () => {
  const response = await api.get('/api/accidents/zones')
  return response.data
}

export const getAccidentStations = async () => {
  const response = await api.get('/api/accidents/stations')
  return response.data
}

export const getAccidentHotspots = async () => {
  const response = await api.get('/api/accidents/hotspots')
  return response.data
}

export const getAccidentTrends = async () => {
  const response = await api.get('/api/accidents/trends')
  return response.data
}

// Violation APIs
export const getMotorVehicleYearly = async () => {
  const response = await api.get('/api/violations/motor-vehicle/yearly')
  return response.data
}

export const getMotorVehicleTop10 = async () => {
  const response = await api.get('/api/violations/motor-vehicle/top-10')
  return response.data
}

export default api
