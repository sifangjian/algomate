import { cardService } from './cardService'

export const statsService = {
  getHallStats: async () => {
    return await cardService.getOverview()
  },
}
