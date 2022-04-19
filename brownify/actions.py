from brownify.models import Track
import numpy as np
import librosa


class Brownifier:
    @staticmethod
    def _is_stereo(track: Track) -> bool:
        return track.num_channels == 2

    @staticmethod
    def _change_pitch_stereo(
        track: Track, n_steps: int, bins_per_octave: int
    ) -> Track:
        track.audio[:, 0] = librosa.effects.pitch_shift(
            track.audio[:, 0],
            track.sample_rate,
            n_steps=n_steps,
            bins_per_octave=bins_per_octave,
        )
        track.audio[:, 1] = librosa.effects.pitch_shift(
            track.audio[:, 1],
            track.sample_rate,
            n_steps=n_steps,
            bins_per_octave=bins_per_octave,
        )
        return track

    @staticmethod
    def _change_pitch_mono(
        track: Track, n_steps: int, bins_per_octave: int
    ) -> Track:
        track.audio = librosa.effects.pitch_shift(
            track.audio,
            track.sample_rate,
            n_steps=n_steps,
            bins_per_octave=bins_per_octave,
        )
        return track

    @staticmethod
    def change_pitch(
        track: Track, n_steps: int, bins_per_octave: int = 12
    ) -> Track:
        """Change the pitch of the track without changing the track speed

        Args:
            track: The track to modify
            n_steps: Number of steps to modify by (positive or negative)
            bins_per_octave: Number of steps in an octave. Defaults to 12.

        Returns:
            The track with the pitch changed
        """
        if Brownifier._is_stereo(track):
            return Brownifier._change_pitch_stereo(
                track, n_steps, bins_per_octave
            )
        else:
            return Brownifier._change_pitch_mono(
                track, n_steps, bins_per_octave
            )

    @staticmethod
    def flat(track: Track) -> Track:
        """Make the track flat by one semitone

        Args:
            track: The track to modify

        Returns:
            The track which is now flat
        """
        return Brownifier.change_pitch(track, n_steps=-1)

    @staticmethod
    def sharp(track: Track) -> Track:
        """Make the track sharp by one semitone

        Args:
            track: The track to modify

        Returns:
            The track which is now sharp
        """
        return Brownifier.change_pitch(track, n_steps=1)

    @staticmethod
    def half_flat(track: Track) -> Track:
        """Make the track flat by one quarter tone

        Args:
            track: The track to modify

        Returns:
            The track which is now half-flat
        """
        return Brownifier.change_pitch(track, n_steps=-1, bins_per_octave=24)

    @staticmethod
    def half_sharp(track: Track) -> Track:
        """Make the track sharp by one quarter tone

        Args:
            track: The track to modify

        Returns:
            The track which is now half-sharp
        """
        return Brownifier.change_pitch(track, n_steps=1, bins_per_octave=24)

    @staticmethod
    def octave_up(track: Track) -> Track:
        """Move the track up by a full octave

        Args:
            track: The track to modify

        Returns:
            The track which is now an octave higher
        """
        return Brownifier.change_pitch(track, n_steps=12)

    @staticmethod
    def octave_down(track: Track) -> Track:
        """Move the track down by a full octave

        Args:
            track: The track to modify

        Returns:
            The track which is now an octave lower
        """
        return Brownifier.change_pitch(track, n_steps=-12)

    @staticmethod
    def time_shift(track: Track, steps: int) -> Track:
        """Shift the track forward or backward in time

        The track is shifted forward or backward in time by rolling the
        values and wrapping where the track ends back to the beginning
        or vice-versa

        Args:
            track: The track to modify
            steps: The number of samples to shift by

        Returns:
            The track which has been shifted in time
        """
        # FIXME: the API should be based on time and it should be calculated
        # based on the track's sample rate.
        track.audio = np.roll(track.audio, steps)
        return track

    @staticmethod
    def early(track: Track) -> Track:
        """Shift the track forward in time by about a tenth of a second

        Args:
            track: The track to modify

        Returns:
            The track which is now early
        """
        # FIXME: should be based on sample rate
        return Brownifier.time_shift(track, -1500)

    @staticmethod
    def late(track: Track) -> Track:
        """Shift a track backward in time by about a tenth of a second

        Args:
            track: The track to modify

        Returns:
            The track which is now late
        """
        # FIXME: should be based on sample rate
        track.audio = np.roll(track.audio, 1500)
        return track
