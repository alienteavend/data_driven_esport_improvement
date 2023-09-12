def find_participant_index_by_puuid(puuid: str, timeline_data: dict):
    return timeline_data['metadata']['participants'].index(puuid)
