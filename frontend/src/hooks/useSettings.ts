import { useState, useCallback } from 'react';
import { settingsApi } from '@/lib/api';
import type {
  Settings,
  SettingsUpdate,
  TimezoneListResponse,
  VLMConnectionTestRequest,
  VLMConnectionTestResponse,
} from '@/types/settings';

export function useSettings() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [timezones, setTimezones] = useState<TimezoneListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSettings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [settingsData, timezonesData] = await Promise.all([
        settingsApi.get(),
        settingsApi.getTimezones(),
      ]);
      setSettings(settingsData);
      setTimezones(timezonesData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch settings');
    } finally {
      setLoading(false);
    }
  }, []);

  const updateSettings = useCallback(async (data: SettingsUpdate) => {
    setSaving(true);
    setError(null);
    try {
      const updated = await settingsApi.update(data);
      setSettings(updated);
      return updated;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update settings';
      setError(message);
      throw err;
    } finally {
      setSaving(false);
    }
  }, []);

  const testVLMConnection = useCallback(
    async (request: VLMConnectionTestRequest): Promise<VLMConnectionTestResponse> => {
      try {
        return await settingsApi.testVLMConnection(request);
      } catch (err) {
        return {
          success: false,
          message: err instanceof Error ? err.message : 'Connection test failed',
          available_models: [],
        };
      }
    },
    []
  );

  return {
    settings,
    timezones,
    loading,
    saving,
    error,
    fetchSettings,
    updateSettings,
    testVLMConnection,
  };
}
